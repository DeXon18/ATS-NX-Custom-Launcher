#
# History
#
# Date          Name                Description of Change
# 10-Jul-2013   Kevin Chen          Creation
# 06-Nov-2013   Jason Fu            Change the rule for command "BEGIN_PROGRAM", "END_PROGRAM", "CALL_PGM" and "SEL TABLE"
#                                   Add "ABST" to a cycle key word
# 23-Feb-2014   Jason Fu            Add new rule for "SPL"
# 17-Mar-2014   Jason Fu            Fix rule for INC_AXIS
# 20-Aug-2015   Shuai Gao           Fix rule for TNC_SYSWRITE, TNC_LABEL_PREFIX, TNC_PI and LENGTH.
# 03-Nov-2015   Shuai Gao           Enhance rules for FN26(TNC_TABOPEN, TNC_TABOPEN_PATH),FN27(TNC_TABWRITE) and FN28(TNC_TABREAD)
# 12-Nov-2015   Shuai Gao           Fix rule for "word : mCode" so that M code can be added into CP command
# 31-Mar-2016   Shuai Gao           Add rules for optionalFilePath and FN16
# 01-Apr-2016   Shuai Gao           Fix the assignment of some parameters in function p_word.
# 13-Apr-2016   Volker Grabowski    PR7539285: Handle different ROUND semantics
# 30-May-2016   Volker Grabowski    PR7726292: Suppress generation of PLY parsetab files
# 25-Jul-2016   Shuai Gao           PR7761731: Enhance rules of "planeParams" with PLANE_RELATIV.
#                                   Add rules of "planeSPA", "planeSPB" and "planeSPC".
# 04-Aug-2016   Shuai Gao           Replace "+" with "PLUS" in p_plcExpr_4 and replace "-" with "MINUS" in p_plcExpr_5.
# 09-Aug-2016   Volker Grabowski    Use custom exception class to handle parse errors
# 02-Sep-2016   Volker Grabowski    Move CseParseError to CSEWrapper.py
# 06-Oct-2016   Volker Grabowski    PR7850582: Implement p_error for proper error handling
# 14-Nov-2016   Shuai Gao           PR7878874: Enhance the rule of p_word_8. Now M138 is supported to parse.
# 31-Jan-2017   Volker Grabowski    PR7254570: Pre-execute NC lines containing RND
# 08-Feb-2017   Volker Grabowski    PR7944855: Use INTEGER cast only for rounding operators

import sys
import cmath
import ply.yacc as yacc

import CseTNC_Lex

from CseTNC_Lex import TNCFuncType as TNCFuncType
from CseTNC_Lex import TNCFuncInfo as TNCFuncInfo
from CseTNC_Lex import TNCWordInfo as TNCWordInfo

if CseTNC_Lex.Core.runInConsole == 0:
    from CSEWrapper import NCBasicType
    from CSEWrapper import VariableManager
    from CSEWrapper import NCExpressionFactory
    from CSEWrapper import CallFactory
    from CSEWrapper import CseParseError

class ExprCore():

    # Get the token map
    tokens = CseTNC_Lex.tokens
    # Parsing rules

    precedence = (
                   ('left', 'PLUS','MINUS'),
                   ('left', 'TIMES','DIVIDE'),
                   ('left', 'POWER'),
                   ('left', 'UN_OP', 'FRAC_OP'),
                   ('right','UMINUS'),
    )

    def __init__(self, debug = 0, callF = None, exprSys = None):
        self.debug = debug
        self.names = { }
        modname = self.__class__.__name__
        self.debugfile = modname + ".dbg"
        self.tabmodule = modname + "_" + "parsetab"

        if CseTNC_Lex.Core.Debug == 1:
            self.parser = yacc.yacc(module=self, debug=self.debug, debugfile=self.debugfile, optimize=0, write_tables=0, tabmodule=self.tabmodule, errorlog = CseTNC_Lex.logger)
        else:
            self.parser = yacc.yacc(module=self, debug=self.debug, debugfile=self.debugfile, optimize=0, write_tables=0, tabmodule=self.tabmodule, errorlog = yacc.NullLogger())

        self.error = None

        if CseTNC_Lex.Core.runInConsole == 0:
            if callF != None:
                self.callFactory = callF
                self.exprSystem = self.callFactory.GetExprSystem()
                self.valueFactory = self.exprSystem.GetValueFactory()
                self.exprFactory = self.exprSystem.GetExprFactory()
            if exprSys != None:
                self.exprSystem = exprSys
                self.valueFactory = self.exprSystem.GetValueFactory()
                self.exprFactory = self.exprSystem.GetExprFactory()

    def SetCallFactory(self, callF):
        self.callFactory = callF
        self.exprSystem = self.callFactory.GetExprSystem()
        self.valueFactory = self.exprSystem.GetValueFactory()
        self.exprFactory = self.exprSystem.GetExprFactory()

    def SetExprSystem(self, exprSys):
        self.exprSystem = exprSys
        self.valueFactory = self.exprSystem.GetValueFactory()
        self.exprFactory = self.exprSystem.GetExprFactory()

    def p_expression_1(self, p):
        '''expression : numExpression'''
        p[0] = p[1]

    def p_expression_2(self, p):
        '''expression : stringExpression'''
        p[0] = p[1]

    def p_numExpression_1(self, p):
        '''numExpression : floatValue'''
        p[0] = self.CreateLiteralExprFromDouble(p[1])

    def p_numExpression_2(self, p):
        '''numExpression : intValue'''
        p[0] = self.CreateLiteralExprFromInteger(p[1])

    def p_numExpression_3(self, p):
        '''numExpression : TNC_PI'''
        p[0] = self.CreateLiteralExprFromDouble(cmath.acos(-1.0).real)

    def p_numExpression_4(self, p):
        '''numExpression : '(' numExpression ')' '''
        p[0] = p[2]

    def p_numExpression_5(self, p):
        '''numExpression : VARIABLE'''
        p[0] = self.exprFactory.CreateVariableExpr(p[1])

    def p_numExpression_6(self, p):
        '''numExpression : UN_OP numExpression'''
        p[0] = self.exprFactory.CreateUnaryArithmeticExpr(p[2], p[1])
        if p[1] == NCExpressionFactory.ROUND_OP or p[1] == NCExpressionFactory.ROUND_DOWN_OP or p[1] == NCExpressionFactory.ROUND_UP_OP:
            p[0] = self.exprFactory.CreateCastExpr(p[0], NCBasicType.INTEGER)

    def p_numExpression_7(self, p):
        '''numExpression : FRAC_OP numExpression'''
        pIntExpr = self.exprFactory.CreateUnaryArithmeticExpr(p[2], NCExpressionFactory.ROUND_DOWN_OP)
        pIntExpr = self.exprFactory.CreateCastExpr(pIntExpr, NCBasicType.INTEGER)
        p[0] = self.exprFactory.CreateBinaryArithmeticExpr(p[2], pIntExpr, NCExpressionFactory.SUB_OP)

    def p_numExpression_8(self, p):
        '''numExpression : numExpression PLUS numExpression'''
        p[0] = self.exprFactory.CreateBinaryArithmeticExpr(p[1], p[3], NCExpressionFactory.ADD_OP)

    def p_numExpression_9(self, p):
        '''numExpression : numExpression MINUS numExpression'''
        p[0] = self.exprFactory.CreateBinaryArithmeticExpr(p[1], p[3], NCExpressionFactory.SUB_OP)

    def p_numExpression_10(self, p):
        '''numExpression : numExpression TIMES numExpression'''
        p[0] = self.exprFactory.CreateBinaryArithmeticExpr(p[1], p[3], NCExpressionFactory.MULT_OP)

    def p_numExpression_11(self, p):
        '''numExpression : numExpression DIVIDE numExpression'''
        pLValue = self.exprFactory.CreateCastExpr(p[1], NCBasicType.DOUBLE)
        p[0] = self.exprFactory.CreateBinaryArithmeticExpr(pLValue, p[3], NCExpressionFactory.DIV_OP)

    def p_numExpression_12(self, p):
        '''numExpression : numExpression POWER numExpression'''
        p[0] = self.exprFactory.CreateBinaryArithmeticExpr(p[1], p[3], NCExpressionFactory.POW_OP)

    def p_numExpression_13(self, p):
        '''numExpression : PLUS numExpression %prec UMINUS'''
        p[0] = p[2]

    def p_numExpression_14(self, p):
        '''numExpression : MINUS numExpression %prec UMINUS'''
        p[0] = self.exprFactory.CreateUnaryArithmeticExpr(p[2], NCExpressionFactory.NEG_OP)

    def p_numExpression_15(self, p):
        '''numExpression : TONUMB_OP '(' SRC STR_VARIABLE ')' '''
        pLValue = self.exprFactory.CreateVariableExpr(p[4])
        p[0] = self.exprFactory.CreateCastExpr(pLValue, NCBasicType.DOUBLE)

    def p_numExpression_16(self, p):
        '''numExpression : STRLEN_OP '(' SRC STR_VARIABLE ')' '''
        pLValue = self.exprFactory.CreateVariableExpr(p[4])
        pExprArray = []
        pExprArray.append(pLValue)

        p[0] = self.exprFactory.CreateMethodExpr("STRLEN", pExprArray)

    def p_numExpression_17(self, p):
        '''numExpression : STRCOMP_OP '(' SRC STR_VARIABLE SEA STR_VARIABLE ')' '''
        pLValue1 = self.exprFactory.CreateVariableExpr(p[4])
        pLValue2 = self.exprFactory.CreateVariableExpr(p[6])
        pExprArray = []
        pExprArray.append(pLValue1)
        pExprArray.append(pLValue2)

        p[0] = self.exprFactory.CreateMethodExpr("STRCOMP", pExprArray)

    def p_numExpression_18(self, p):
        '''numExpression : INSTR_OP '(' SRC STR_VARIABLE SEA STR_VARIABLE BEG numExpression ')' '''
        pLValue1 = self.exprFactory.CreateVariableExpr(p[4])
        pLValue2 = self.exprFactory.CreateVariableExpr(p[6])
        pExprArray = []
        pExprArray.append(pLValue1)
        pExprArray.append(pLValue2)
        pExprArray.append(p[8])

        p[0] = self.exprFactory.CreateMethodExpr("INSTR", pExprArray)

    def p_stringExpression_1(self, p):
        '''stringExpression : STRING'''
        p[0] = self.CreateLiteralExprFromString(p[1])

    def p_stringExpression_2(self, p):
        '''stringExpression : stringExpression QS_CHAINLINK_OP stringExpression'''
        p[0] = self.exprFactory.CreateBinaryArithmeticExpr(p[1], p[3], NCExpressionFactory.ADD_OP)

    def p_stringExpression_3(self, p):
        '''stringExpression : SUBSTR_OP '(' SRC STR_VARIABLE BEG numExpression LENGTH numExpression ')' '''
        pLValue1 = self.exprFactory.CreateVariableExpr(p[4])
        pExprArray = []
        pExprArray.append(pLValue1)
        pExprArray.append(p[6])
        pExprArray.append(p[8])

        p[0] = self.exprFactory.CreateMethodExpr("SUBSTR", pExprArray)

    def p_stringExpression_4(self, p):
        '''stringExpression : TOCHAR_OP '(' DAT numExpression DECIMALS numExpression ')' '''
        pLValue1 = self.exprFactory.CreateCastExpr(p[4], NCBasicType.DOUBLE)
        pExprArray = []
        pExprArray.append(pLValue1)
        pExprArray.append(p[6])

        p[0] = self.exprFactory.CreateMethodExpr("TOCHAR", pExprArray)

    def p_stringExpression_5(self, p):
        '''stringExpression : STR_VARIABLE'''
        p[0] = self.exprFactory.CreateVariableExpr(p[1])

    def p_stringExpression_6(self, p):
        '''stringExpression : '(' stringExpression ')' '''
        p[0] = p[2]

    def p_intValue(self, p):
        '''intValue : INTEGER_VALUE'''
        p[0] = int(p[1])

    def p_floatValue(self, p):
        '''floatValue : FLOAT_VALUE'''
        p[0] = float(p[1])

    def p_error(self, p):
        self.error = ""

    def CreateLiteralExprFromInteger(self, p):
        return self.exprFactory.CreateLiteral(self.valueFactory.CreateIntegerValue(p))

    def CreateLiteralExprFromBool(self, p):
        return self.exprFactory.CreateLiteral(self.valueFactory.CreateBoolValue(p))

    def CreateLiteralExprFromString(self, p):
        return self.exprFactory.CreateLiteral(self.valueFactory.CreateStringValue(p))

    def CreateLiteralExprFromDouble(self, p):
        return self.exprFactory.CreateLiteral(self.valueFactory.CreateDoubleValue(p))


class Parser(ExprCore):

    start = 'line'

    def p_line_1(self, p):
        '''line : ncLine'''

    def p_line_2(self, p):
        '''line : ncLine EOL'''

    def p_ncLine_1(self, p):
        '''ncLine : linePrefix lineNumber lineContent optionalComment'''

    def p_linePrefix_1(self, p):
        '''linePrefix : '''

    def p_linePrefix_2(self, p):
        '''linePrefix : DIVIDE '''
        self.callFactory.CreateBreakCall(-1)

    def p_lineNumber_1(self, p):
        '''lineNumber : '''

    def p_lineNumber_2(self, p):
        '''lineNumber : intValue'''

    def p_start_path_state(self, p):
        '''start_path_state : '''
        CseTNC_Lex.start_path(p.lexer)

    def p_end_path_state(self, p):
        '''end_path_state : '''
        p[0] = CseTNC_Lex.get_path(p.lexer)

    def p_start_programName_state(self, p):
        '''start_programName_state : '''
        CseTNC_Lex.start_programName(p.lexer)

    def p_end_programName_state(self, p):
        '''end_programName_state : '''
        p[0] = CseTNC_Lex.get_programName(p.lexer)

    def p_start_selectionName_state(self, p):
        '''start_selectionName_state : '''
        CseTNC_Lex.start_selectionName(p.lexer)

    def p_end_selectionName_state(self, p):
        '''end_selectionName_state : '''
        p[0] = CseTNC_Lex.get_selectionName(p.lexer)
        
    def p_lineContent_1(self, p):
        '''lineContent : start_programName_state BEGIN_PROGRAM end_programName_state UNIT'''
        dictArgsNC = {}
        dictArgsNC["Name"] = self.CreateLiteralExprFromString(p[3])

        if p[4] == "MM_MEASURE":
            pExpr = self.CreateLiteralExprFromString("MM")
        elif p[4] == "INCH_MEASURE":
            pExpr = self.CreateLiteralExprFromString("INCH")
        
        dictArgsNC["Unit"] = pExpr
        self.callFactory.CreateMetacodeCall("BEGIN_PGM", dictArgsNC)

    def p_lineContent_2(self, p):
        '''lineContent : start_programName_state END_PROGRAM end_programName_state UNIT'''
        dictArgsNC = {}
        dictArgsNC["Name"] = self.CreateLiteralExprFromString(p[3])

        if p[4] == "MM_MEASURE":
            pExpr = self.CreateLiteralExprFromString("MM")
        elif p[4] == "INCH_MEASURE":
            pExpr = self.CreateLiteralExprFromString("INCH")
        
        dictArgsNC["Unit"] = pExpr

        self.callFactory.CreateMetacodeCall("END_PGM", dictArgsNC)

    def p_lineContent_3(self, p):
        '''lineContent : BLK_FORM FLOAT_VALUE axisWord axisWord axisWord lineContent'''

    def p_lineContent_4(self, p):
        '''lineContent : BLK_FORM FLOAT_VALUE AXIS axisWord axisWord axisWord lineContent'''

    def p_lineContent_5(self, p):
        '''lineContent : _embed4_lineContent FUNC wordList'''

    def p_embed4_lineContent(self, p):
        '''_embed4_lineContent : '''
        if last_token.type != 'FUNC':
            pass

        func = last_token.value
        CseTNC_Lex.Core.g_nCurFunc = func.nID
        if CseTNC_Lex.Core.g_nCurFunc == TNCFuncType.FUNC_TCPM or CseTNC_Lex.Core.g_nCurFunc == TNCFuncType.FUNC_TCPM_RESET:
            dictArgsNC = {}
            dictArgsNC["Value"] = self.CreateLiteralExprFromString(func.pszName)
            self.callFactory.CreateMetacodeCall("FUNCTION", dictArgsNC)
        else:
            self.callFactory.CreateMetacodeCall(func.pszName)

    def p_lineContent_6(self, p):
        '''lineContent : FUNC_APPR_DEP _embed5_lineContent FUNC wordList'''

    def p_embed5_lineContent(self, p):
        '''_embed5_lineContent : '''
        if last_token.type != 'FUNC':
            pass

        func = last_token.value
        CseTNC_Lex.Core.g_nCurFunc = func.nID
        self.callFactory.CreateMetacodeCall(p[-1])
        self.callFactory.CreateMetacodeCall(func.pszName)

    def p_lineContent_7(self, p):
        '''lineContent : _embed6_lineContent FUNC_ARG  numExpression _embed7_lineContent wordList'''

    def p_embed6_lineContent(self, p):
        '''_embed6_lineContent : '''
        if last_token.type != 'FUNC_ARG':
            pass

        func = last_token.value
        CseTNC_Lex.Core.g_nCurFunc =func.nID

    def p_embed7_lineContent(self, p):
        '''_embed7_lineContent : '''
        dictArgsNC = {}
        dictArgsNC["Value"] = p[-1]
        self.callFactory.CreateMetacodeCall(p[-2].pszName, dictArgsNC)

    def p_lineContent_8(self, p):
        '''lineContent : wordList'''

    def p_lineContent_9(self, p):
        '''lineContent : toolDef'''

    def p_lineContent_10(self, p):
        '''lineContent : toolCall'''

    def p_lineContent_11(self, p):
        '''lineContent : selections'''

    def p_lineContent_12(self, p):
        '''lineContent : cycleDef'''

    def p_lineContent_13(self, p):
        '''lineContent : cycleCall'''
        
    def p_lineContent_14(self, p):
        '''lineContent : TNC_LABEL'''
        self.callFactory.CreateLabelCall(p[1])
        dictArgsNC = {}
        dictArgsNC["Value"] = self.CreateLiteralExprFromString(p[1])
        self.callFactory.CreateMetacodeCall("LBL", dictArgsNC)

    def p_lineContent_15(self, p):
        '''lineContent : CALL TNC_LABEL repeat'''
        dictArgsNC = {}
        dictArgsNC["Label"] = self.CreateLiteralExprFromString(p[2])
        dictArgsNC["Repeat"] = self.CreateLiteralExprFromInteger(p[3])
        self.callFactory.CreateMetacodeCall("CALL", dictArgsNC)

    def p_lineContent_16(self, p):
        '''lineContent : start_programName_state CALL_PGM end_programName_state'''
        dictArgsNC = {}
        dictArgsNC["Program"] = self.CreateLiteralExprFromString(p[3])
        self.callFactory.CreateMetacodeCall("CALL_PGM", dictArgsNC)

    def p_lineContent_17(self, p):
        '''lineContent : assignment'''

    def p_lineContent_18(self, p):
        '''lineContent : calcFunc'''

    def p_lineContent_19(self, p):
        '''lineContent : planeCall'''

    def p_lineContent_20(self, p):
        '''lineContent : declareSTR'''

    def p_lineContent_21(self, p):
        '''lineContent : SPLFunc'''

    def p_path_1(self, p):
        '''path : STRING'''
        p[0] = p[1]

    def p_optionalComment_1(self, p):
        '''optionalComment : '''

    def p_optionalComment_2(self, p):
        '''optionalComment : COMMENT'''

    def p_wordList_1(self, p):
        '''wordList : '''

    def p_wordList_2(self, p):
        '''wordList : word wordList'''

    def p_word_1(self, p):
        '''word : axisWord'''
        p[0] = TNCWordInfo("", None)
        
        nCurFunc = CseTNC_Lex.Core.g_nCurFunc
        if nCurFunc == TNCFuncType.FUNC_NONE or nCurFunc == TNCFuncType.FUNC_LN or nCurFunc == TNCFuncType.FUNC_L or\
        nCurFunc == TNCFuncType.FUNC_LT or nCurFunc == TNCFuncType.FUNC_CT or nCurFunc == TNCFuncType.FUNC_LCT or\
        nCurFunc == TNCFuncType.FUNC_C or nCurFunc == TNCFuncType.FUNC_CR or nCurFunc == TNCFuncType.FUNC_CC or\
        nCurFunc == TNCFuncType.FUNC_CP:
            dictArgsNC = {}
            dictArgsNC["Value"] = p[1].pValue
            self.callFactory.CreateMetacodeCall(p[1].pszName, dictArgsNC)
            
        elif nCurFunc == TNCFuncType.FUNC_CYCLE_AXIS_INCAXIS_HASH:
            p[0].pszName = p[1].pszName
            p[0].pValue = p[1].pValue

        elif nCurFunc == TNCFuncType.FUNC_CYCLE_A_B_C:
            if p[1].pszName == 'A' or p[1].pszName == 'B' or p[1].pszName == 'C':
                p[0].pszName = p[1].pszName
                p[0].pValue = p[1].pValue
            else:
                self.error = ""
                raise CseParseError

        elif nCurFunc == TNCFuncType.FUNC_CYCLE_X:
            if p[1].pszName == 'X':
                p[0].pszName = p[1].pszName
                p[0].pValue = p[1].pValue
            else:
                self.error = ""
                raise CseParseError

        elif nCurFunc == TNCFuncType.FUNC_CYCLE_Y:
            if p[1].pszName == 'Y':
                p[0].pszName = p[1].pszName
                p[0].pValue = p[1].pValue
            else:
                self.error = ""
                raise CseParseError

        elif nCurFunc == TNCFuncType.FUNC_CYCLE_X_Y_CCX_CCY:
            if p[1].pszName == 'X' or p[1].pszName == 'Y':
                p[0].pszName = p[1].pszName
                p[0].pValue = p[1].pValue
            else:
                self.error = ""
                raise CseParseError

        elif nCurFunc == TNCFuncType.FUNC_CYCLE_X_Y_Z or nCurFunc == TNCFuncType.FUNC_CYCLE_DATUMPLANE:
            if p[1].pszName == 'X' or p[1].pszName == 'Y' or p[1].pszName == 'Z':
                p[0].pszName = p[1].pszName
                p[0].pValue = p[1].pValue
            else:
                self.error = ""
                raise CseParseError

        else:
            self.error = ""
            raise CseParseError

    def p_word_2(self, p):
        '''word : INC_AXIS numExpression'''
        p[0] = TNCWordInfo("", None)

        nCurFunc = CseTNC_Lex.Core.g_nCurFunc
        if nCurFunc == TNCFuncType.FUNC_NONE or nCurFunc == TNCFuncType.FUNC_LN or nCurFunc == TNCFuncType.FUNC_L or\
        nCurFunc == TNCFuncType.FUNC_LT or nCurFunc == TNCFuncType.FUNC_CT or nCurFunc == TNCFuncType.FUNC_LCT or\
        nCurFunc == TNCFuncType.FUNC_C or nCurFunc == TNCFuncType.FUNC_CR or nCurFunc == TNCFuncType.FUNC_CC or\
        nCurFunc == TNCFuncType.FUNC_CP:
            dictArgsNC = {}
            dictArgsNC["Value"] = p[2]
            self.callFactory.CreateMetacodeCall(p[1], dictArgsNC)

        elif nCurFunc == TNCFuncType.FUNC_CYCLE_AXIS_INCAXIS_HASH:
            p[0].pszName = p[1]
            p[0].pValue = p[2]
        else:
            self.error = ""
            raise CseParseError

    def p_word_3(self, p):
        '''word : normalWord'''
        p[0] = TNCWordInfo("", None)

        nCurFunc = CseTNC_Lex.Core.g_nCurFunc
        if nCurFunc == TNCFuncType.FUNC_NONE or nCurFunc == TNCFuncType.FUNC_LN:
            dictArgsNC = {}
            dictArgsNC["Value"] = p[1].pValue
            self.callFactory.CreateMetacodeCall(p[1].pszName, dictArgsNC)
        else:
            self.error = ""
            raise CseParseError

    def p_word_4(self, p):
        '''word : toolDirWord'''
        p[0] = TNCWordInfo("", None)

        nCurFunc = CseTNC_Lex.Core.g_nCurFunc
        if nCurFunc == TNCFuncType.FUNC_NONE or nCurFunc == TNCFuncType.FUNC_LN:
            dictArgsNC = {}
            dictArgsNC["Value"] = p[1].pValue
            self.callFactory.CreateMetacodeCall(p[1].pszName, dictArgsNC)
        else:
            self.error = ""
            raise CseParseError


    def p_word_5(self, p):
        '''word : F_PARAM'''
        p[0] = TNCWordInfo("", None)

        nCurFunc = CseTNC_Lex.Core.g_nCurFunc
        if nCurFunc == TNCFuncType.FUNC_TCPM:
            dictArgsNC = {}
            dictArgsNC["Value"] = self.CreateLiteralExprFromString(p[1])
            self.callFactory.CreateMetacodeCall("F", dictArgsNC)
        else:
            self.error = ""
            raise CseParseError

    def p_word_6(self, p):
        '''word : AXIS_PARAM'''
        p[0] = TNCWordInfo()

        nCurFunc = CseTNC_Lex.Core.g_nCurFunc
        if nCurFunc == TNCFuncType.FUNC_TCPM:
            dictArgsNC = {}
            dictArgsNC["Value"] = self.CreateLiteralExprFromString(p[1])
            self.callFactory.CreateMetacodeCall("AXIS", dictArgsNC)
        else:
            self.error = ""
            raise CseParseError

    def p_word_7(self, p):
        '''word : PATHCTRL_PARAM'''
        p[0] = TNCWordInfo()

        nCurFunc = CseTNC_Lex.Core.g_nCurFunc
        if nCurFunc == TNCFuncType.FUNC_TCPM:
            dictArgsNC = {}
            dictArgsNC["Value"] = self.CreateLiteralExprFromString(p[1])
            self.callFactory.CreateMetacodeCall("PATHCTRL", dictArgsNC)
        else:
            self.error = ""
            raise CseParseError

    def p_word_8(self, p):
        '''word : mCode cycleAxisList'''
        p[0] = TNCWordInfo()

        nCurFunc = CseTNC_Lex.Core.g_nCurFunc
        if nCurFunc == TNCFuncType.FUNC_NONE or nCurFunc == TNCFuncType.FUNC_LN or nCurFunc == TNCFuncType.FUNC_L or\
        nCurFunc == TNCFuncType.FUNC_LP or nCurFunc == TNCFuncType.FUNC_CT or nCurFunc == TNCFuncType.FUNC_C or\
        nCurFunc == TNCFuncType.FUNC_CR or nCurFunc == TNCFuncType.FUNC_CP:
            if p[1].GetValue().GetString() == "M138":
                if self.callFactory.IsMetacodeDefined("M138"):
                    self.callFactory.CreateMetacodeCall("M138", listArgs = p[2])
            else:
                if len(p[2]) == 0:
                    if self.callFactory.IsMetacodeDefined(p[1].GetValue().GetString()):
                        self.callFactory.CreateDynamicMetacodeCall(p[1])
                else:
                    self.error = ""
                    raise CseParseError
        else:
            self.error = ""
            raise CseParseError

    def p_word_9(self, p):
        '''word : FEED feedExpr'''
        p[0] = TNCWordInfo()

        nCurFunc = CseTNC_Lex.Core.g_nCurFunc
        if nCurFunc == TNCFuncType.FUNC_NONE or nCurFunc == TNCFuncType.FUNC_LN or nCurFunc == TNCFuncType.FUNC_L or\
           nCurFunc == TNCFuncType.FUNC_LP or nCurFunc == TNCFuncType.FUNC_LT or nCurFunc == TNCFuncType.FUNC_LCT or\
           nCurFunc == TNCFuncType.FUNC_PCT or nCurFunc == TNCFuncType.FUNC_CHF or nCurFunc == TNCFuncType.FUNC_C or\
           nCurFunc == TNCFuncType.FUNC_CC or nCurFunc == TNCFuncType.FUNC_CP or nCurFunc == TNCFuncType.FUNC_CT:
            dictArgsNC = {}
            dictArgsNC["Value"] = p[2]
            self.callFactory.CreateMetacodeCall("F", dictArgsNC)
        elif nCurFunc == TNCFuncType.FUNC_RND:
            dictArgsNC = {}
            dictArgsNC["Value"] = p[2]
            self.callFactory.CreateMetacodeCall("F_RND", dictArgsNC)
        elif nCurFunc == TNCFuncType.FUNC_CYCLE_VALUE_F or nCurFunc == TNCFuncType.FUNC_CYCLE_F or\
            nCurFunc == TNCFuncType.FUNC_CYCLE_F_DR or nCurFunc == TNCFuncType.FUNC_CYCLE_F_DR_RADIUS or\
            nCurFunc == TNCFuncType.FUNC_CYCLE_A_B_C:
            p[0].pszName = p[1]
            p[0].pValue = p[2]
        else:
            self.error = ""
            raise CseParseError

    def p_word_10(self, p):
        '''word : MB feedExpr'''
        p[0] = TNCWordInfo()

        nCurFunc = CseTNC_Lex.Core.g_nCurFunc
        if nCurFunc == TNCFuncType.FUNC_NONE or nCurFunc == TNCFuncType.FUNC_LN or nCurFunc == TNCFuncType.FUNC_L or\
           nCurFunc == TNCFuncType.FUNC_LT or nCurFunc == TNCFuncType.FUNC_CT or nCurFunc == TNCFuncType.FUNC_LCT or\
           nCurFunc == TNCFuncType.FUNC_CHF or nCurFunc == TNCFuncType.FUNC_CC or nCurFunc == TNCFuncType.FUNC_C or\
           nCurFunc == TNCFuncType.FUNC_CR or nCurFunc == TNCFuncType.FUNC_LP:
            dictArgsNC = {}
            dictArgsNC["Value"] = p[2]
            self.callFactory.CreateMetacodeCall("MB", dictArgsNC)
        elif nCurFunc == TNCFuncType.FUNC_RND:
            dictArgsNC = {}
            dictArgsNC["Value"] = p[2]
            self.callFactory.CreateMetacodeCall("MB_RND", dictArgsNC)
        else:
            self.error = ""
            raise CseParseError

    def p_word_11(self, p):
        '''word : R_WORD optionalDoubleExpr'''
        p[0] = TNCWordInfo()

        nCurFunc = CseTNC_Lex.Core.g_nCurFunc
        if nCurFunc == TNCFuncType.FUNC_NONE or nCurFunc == TNCFuncType.FUNC_L or nCurFunc == TNCFuncType.FUNC_C or\
           nCurFunc == TNCFuncType.FUNC_CT or nCurFunc == TNCFuncType.FUNC_LCT or nCurFunc == TNCFuncType.FUNC_PCT or\
           nCurFunc == TNCFuncType.FUNC_CR or nCurFunc == TNCFuncType.FUNC_LP or nCurFunc == TNCFuncType.FUNC_LN:
            dictArgsNC = {}
            dictArgsNC["Value"] = p[2]
            self.callFactory.CreateMetacodeCall("R", dictArgsNC)
        elif nCurFunc == TNCFuncType.FUNC_RND:
            dictArgsNC = {}
            dictArgsNC["Value"] = p[2]
            self.callFactory.CreateMetacodeCall("R_RND", dictArgsNC)
        else:
            self.error = ""
            raise CseParseError

    def p_word_12(self, p):
        '''word : RADIUS_CORR'''
        p[0] = TNCWordInfo()

        nCurFunc = CseTNC_Lex.Core.g_nCurFunc
        if nCurFunc == TNCFuncType.FUNC_NONE or nCurFunc == TNCFuncType.FUNC_L or nCurFunc == TNCFuncType.FUNC_LT or\
        nCurFunc == TNCFuncType.FUNC_LN or nCurFunc == TNCFuncType.FUNC_C or nCurFunc == TNCFuncType.FUNC_CP or\
        nCurFunc == TNCFuncType.FUNC_CT or nCurFunc == TNCFuncType.FUNC_LCT or nCurFunc == TNCFuncType.FUNC_PCT or\
        nCurFunc == TNCFuncType.FUNC_LP:
             self.callFactory.CreateMetacodeCall(p[1])
        else:
            self.error = ""
            raise CseParseError

    def p_word_13(self, p):
        '''word : LENGTH numExpression'''
        p[0] = TNCWordInfo()

        nCurFunc = CseTNC_Lex.Core.g_nCurFunc
        if nCurFunc == TNCFuncType.FUNC_NONE or nCurFunc == TNCFuncType.FUNC_LN or nCurFunc == TNCFuncType.FUNC_LT:
            dictArgsNC = {}
            dictArgsNC["Value"] = p[2]
            self.callFactory.CreateMetacodeCall("LEN", dictArgsNC)
        else:
            self.error = ""
            raise CseParseError

    def p_word_14(self, p):
        '''word : CENTER_ANGLE numExpression'''
        p[0] = TNCWordInfo()

        nCurFunc = CseTNC_Lex.Core.g_nCurFunc
        if nCurFunc == TNCFuncType.FUNC_NONE or nCurFunc == TNCFuncType.FUNC_CT or nCurFunc == TNCFuncType.FUNC_PCT:
            dictArgsNC = {}
            dictArgsNC["Value"] = p[2]
            self.callFactory.CreateMetacodeCall("CCA", dictArgsNC)
        else:
            self.error = ""
            raise CseParseError

    def p_word_15(self, p):
        '''word : ROT_DIR direction'''
        p[0] = TNCWordInfo()

        nCurFunc = CseTNC_Lex.Core.g_nCurFunc
        if nCurFunc == TNCFuncType.FUNC_NONE or nCurFunc == TNCFuncType.FUNC_C or nCurFunc == TNCFuncType.FUNC_CR or nCurFunc == TNCFuncType.FUNC_CP:
            dictArgsNC = {}
            dictArgsNC["Value"] = self.CreateLiteralExprFromBool(p[2])
            self.callFactory.CreateMetacodeCall(p[1], dictArgsNC)
        elif nCurFunc == TNCFuncType.FUNC_CYCLE_F_DR or nCurFunc == TNCFuncType.FUNC_CYCLE_F_DR_RADIUS:
            p[0].pszName = p[1]
            p[0].pValue = self.CreateLiteralExprFromBool(p[2])
        else:
            self.error = ""
            raise CseParseError

    def p_word_16(self, p):
        '''word : POLAR_RADIUS numExpression'''
        p[0] = TNCWordInfo()
        
        nCurFunc = CseTNC_Lex.Core.g_nCurFunc
        if nCurFunc == TNCFuncType.FUNC_NONE or nCurFunc == TNCFuncType.FUNC_LP or nCurFunc == TNCFuncType.FUNC_CTP or nCurFunc == TNCFuncType.FUNC_PCT:
            dictArgsNC = {}
            dictArgsNC["Value"] = p[2]
            self.callFactory.CreateMetacodeCall("PR", dictArgsNC)
        else:
            self.error = ""
            raise CseParseError

    def p_word_17(self, p):
        '''word : POLAR_ANGLE numExpression'''
        p[0] = TNCWordInfo()

        nCurFunc = CseTNC_Lex.Core.g_nCurFunc
        if nCurFunc == TNCFuncType.FUNC_NONE or nCurFunc == TNCFuncType.FUNC_LP or nCurFunc == TNCFuncType.FUNC_CTP or\
            nCurFunc == TNCFuncType.FUNC_PCT or nCurFunc == TNCFuncType.FUNC_CP:
            dictArgsNC = {}
            dictArgsNC["Value"] = p[2]
            self.callFactory.CreateMetacodeCall("PA", dictArgsNC)
        else:
            self.error = ""
            raise CseParseError

    def p_word_18(self, p):
        '''word : INC_POLAR_ANGLE numExpression'''
        p[0] = TNCWordInfo()

        nCurFunc = CseTNC_Lex.Core.g_nCurFunc
        if nCurFunc == TNCFuncType.FUNC_NONE or nCurFunc == TNCFuncType.FUNC_LP or\
            nCurFunc == TNCFuncType.FUNC_C or nCurFunc == TNCFuncType.FUNC_CP:
            dictArgsNC = {}
            dictArgsNC["Value"] = p[2]
            self.callFactory.CreateMetacodeCall("IPA", dictArgsNC)
        else:
            self.error = ""
            raise CseParseError

    def p_word_19(self, p):
        '''word : STOP'''
        p[0] = TNCWordInfo()
        self.callFactory.CreateMetacodeCall("STOP")

    def p_word_20(self, p):
        '''word : T_WORD expression'''
        p[0] = TNCWordInfo()

        nCurFunc = CseTNC_Lex.Core.g_nCurFunc
        if nCurFunc == TNCFuncType.FUNC_CYCLE_T:
            p[0].pszName = 'T'
            p[0].pValue = p[2]
        else:
            self.error = ""
            raise CseParseError

    def p_word_21(self, p):
        '''word : HASH_WORD numExpression'''
        p[0] = TNCWordInfo()

        nCurFunc = CseTNC_Lex.Core.g_nCurFunc
        if nCurFunc == TNCFuncType.FUNC_CYCLE_AXIS_INCAXIS_HASH:
            p[0].pszName = 'Hash'
            p[0].pValue = p[2]
        else:
            self.error = ""
            raise CseParseError

    def p_word_22(self, p):
        '''word : RADIUS_WORD numExpression'''
        p[0] = TNCWordInfo()

        nCurFunc = CseTNC_Lex.Core.g_nCurFunc
        if nCurFunc == TNCFuncType.FUNC_CYCLE_F_DR_RADIUS:
            p[0].pszName = 'RADIUS'
            p[0].pValue = p[2]
        else:
            self.error = ""
            raise CseParseError

    def p_word_23(self, p):
        '''word : ROT_WORD numExpression'''
        p[0] = TNCWordInfo()

        nCurFunc = CseTNC_Lex.Core.g_nCurFunc
        if nCurFunc == TNCFuncType.FUNC_CYCLE_ROT_IROT:
            p[0].pszName = 'ROT'
            p[0].pValue = p[2]
        else:
            self.error = ""
            raise CseParseError

    def p_word_24(self, p):
        '''word : IROT_WORD numExpression'''
        p[0] = TNCWordInfo()

        nCurFunc = CseTNC_Lex.Core.g_nCurFunc
        if nCurFunc == TNCFuncType.FUNC_CYCLE_ROT_IROT:
            p[0].pszName = 'IROT'
            p[0].pValue = p[2]
        else:
            self.error = ""
            raise CseParseError

    def p_word_25(self, p):
        '''word : CCX_WORD numExpression'''
        p[0] = TNCWordInfo()

        nCurFunc = CseTNC_Lex.Core.g_nCurFunc
        if nCurFunc == TNCFuncType.FUNC_CYCLE_X_Y_CCX_CCY:
            p[0].pszName = 'CCX'
            p[0].pValue = p[2]
        else:
            self.error = ""
            raise CseParseError

    def p_word_26(self, p):
        '''word : CCY_WORD numExpression'''
        p[0] = TNCWordInfo()

        nCurFunc = CseTNC_Lex.Core.g_nCurFunc
        if nCurFunc == TNCFuncType.FUNC_CYCLE_X_Y_CCX_CCY:
            p[0].pszName = 'CCY'
            p[0].pValue = p[2]
        else:
            self.error = ""
            raise CseParseError

    def p_word_27(self, p):
        '''word : LOOKAHEAD numExpression'''
        p[0] = TNCWordInfo()
        dictArgsNC = {}
        dictArgsNC["Value"] = p[2]
        self.callFactory.CreateMetacodeCall('LA', dictArgsNC)

    def p_word_28(self, p):
        '''word : ABST_OP numExpression'''
        p[0] = TNCWordInfo("ABST", p[2])

    def p_axisWord_1(self, p):
        '''axisWord : AXIS numExpression'''
        p[0] = TNCWordInfo(p[1], p[2])

    def p_normalWord_1(self, p):
        '''normalWord : NORMAL numExpression'''
        p[0] = TNCWordInfo(p[1], p[2])

    def p_toolDirWord_1(self, p):
        '''toolDirWord : TOOLDIR numExpression'''
        p[0] = TNCWordInfo(p[1], p[2])

    def p_mCode_1(self, p):
        '''mCode : MFUNC'''
        p[0] = self.CreateLiteralExprFromString(p[1])

    def p_mCode_2(self, p):
        '''mCode : 'M' variable'''
        pIntExpr = self.exprFactory.CreateCastExpr(p[2], NCBasicType.INTEGER)
        p[0] = self.exprFactory.CreateBinaryArithmeticExpr(self.CreateLiteralExprFromString("M"), pIntExpr, NCExpressionFactory.ADD_OP)

    def p_feedExpr_1(self, p):
        '''feedExpr : '''
        p[0] = self.CreateLiteralExprFromDouble(0.0)

    def p_feedExpr_2(self, p):
        '''feedExpr : TNC_MAX'''
        p[0] = self.CreateLiteralExprFromDouble(-1.0)

    def p_feedExpr_3(self, p):
        '''feedExpr : AUTO'''
        p[0] = self.CreateLiteralExprFromDouble(-2.0)

    def p_feedExpr_4(self, p):
        '''feedExpr : numExpression'''
        p[0] = p[1]

    def p_direction_1(self, p):
        '''direction : PLUS '''
        p[0] = True

    def p_direction_2(self, p):
        '''direction : MINUS '''
        p[0] = False

    def p_toolDef_1(self, p):
        '''toolDef : TOOL_DEF optionalToolName optionalLength optionalRadius'''
        dictArgsNC = {}

        if p[2] != None:
            dictArgsNC["Value"] = p[2]
        if p[3] != None:
            dictArgsNC["Length"] = p[3]
        if p[4] != None:
            dictArgsNC["Radius"] = p[4]

        self.callFactory.CreateMetacodeCall("TOOL_DEF", dictArgsNC)

    def p_optionalDoubleExpr_1(self, p):
        '''optionalDoubleExpr : '''
        p[0] = self.CreateLiteralExprFromDouble(0.0)

    def p_optionalDoubleExpr_2(self, p):
        '''optionalDoubleExpr : numExpression'''
        p[0] = p[1]

    def p_optionalLength_1(self, p):
        '''optionalLength : '''
        p[0] = None

    def p_optionalLength_2(self, p):
        '''optionalLength : FUNC numExpression'''
        if p[1].nID != TNCFuncType.FUNC_L:
            self.error = ""
            raise CseParseError
        p[0] = p[2]

    def p_optionalRadius_1(self, p):
        '''optionalRadius : '''
        p[0] = None

    def p_optionalRadius_2(self, p):
        '''optionalRadius : R_WORD numExpression'''
        p[0] = p[2]

    def p_toolCall_1(self, p):
        '''toolCall : TOOL_CALL optionalToolName optionalAxis optionalSpindleSpeed optionalFeed optionalRotDir optionalRotDir optionalRotDir'''
        dictArgsNC = {}
        if p[2] != None:
            dictArgsNC["Value"] = p[2]
        if p[3] != "":
            dictArgsNC["Axis"] = self.CreateLiteralExprFromString(p[3])
        if p[4] != None:
            dictArgsNC["SpindleSpeed"] = p[4]
        if p[5] != None:
            dictArgsNC["Feed"] = p[5]
        if p[6].pValue != None:
            dictArgsNC[p[6].pszName] = p[6].pValue
        if p[7].pValue != None:
            dictArgsNC[p[7].pszName] = p[7].pValue
        if p[8].pValue != None:
            dictArgsNC[p[8].pszName] = p[8].pValue
         
        if len(dictArgsNC) == 0:
            self.error = ""
            raise CseParseError

        self.callFactory.CreateMetacodeCall("TOOL_CALL", dictArgsNC)

    def p_selections_1(self, p):
        '''selections : start_selectionName_state SEL_TABLE end_selectionName_state'''
        dictArgsNC = {}
        dictArgsNC["Value"] = self.CreateLiteralExprFromString(p[3])
        self.callFactory.CreateMetacodeCall("SEL_TABLE", dictArgsNC)
        
    def p_optionalToolName_1(self, p):
        '''optionalToolName : '''
        p[0] = None

    def p_optionalToolName_2(self, p):
        '''optionalToolName : intValue'''
        p[0] = self.CreateLiteralExprFromInteger(p[1])

    def p_optionalToolName_3(self, p):
        '''optionalToolName : FLOAT_VALUE'''
        p[0] = self.CreateLiteralExprFromDouble(p[1])

    def p_optionalToolName_4(self, p):
        '''optionalToolName : STRING'''
        p[0] = self.CreateLiteralExprFromString(p[1])

    def p_optionalToolName_5(self, p):
        '''optionalToolName : variable'''
        p[0] = p[1]

    def p_optionalAxis_1(self, p):
        '''optionalAxis : '''
        p[0] = ""

    def p_optionalAxis_2(self, p):
        '''optionalAxis : AXIS'''
        p[0] = p[1]

    def p_optionalSpindleSpeed_1(self, p):
        '''optionalSpindleSpeed : '''
        p[0] = None

    def p_optionalSpindleSpeed_2(self, p):
        '''optionalSpindleSpeed : TNC_SPINDLE numExpression'''
        p[0] = p[2]

    def p_optionalFeed_1(self, p):
        '''optionalFeed : '''
        p[0] = None

    def p_optionalFeed_2(self, p):
        '''optionalFeed : FEED feedExpr'''
        p[0] = p[2]

    def p_optionalRotDir_1(self, p):
        '''optionalRotDir : '''
        p[0] = TNCWordInfo()

    def p_optionalRotDir_2(self, p):
        '''optionalRotDir : ROT_DIR numExpression'''
        p[0] = TNCWordInfo(p[1], p[2])

    def p_cycleDef_1(self, p):
        '''cycleDef : CYCLE_DEF_VOID cycleKeyword'''
        self.generateCycleDefMetacode(p[1].nCycleID, p[1].nCycleSubID, "CYCL_DEF_")

    def p_cycleDef_2(self, p):
        '''cycleDef : cycleDefArgumentList cycleKeyword cycleArgumentList'''
        self.generateCycleDefMetacode(p[1].nCycleID, p[1].nCycleSubID, "CYCL_DEF_", p[3])

    def p_cycleDef_3(self, p):
        '''cycleDef : cycleDefArgumentList cycleKeyword'''
        self.generateCycleDefMetacode(p[1].nCycleID, p[1].nCycleSubID, "CYCL_DEF_")

    def p_cycleDef_4(self, p):
        '''cycleDef : CYCLE_DEF_INDEXLIST cycleKeyword cycleIndexList'''
        self.generateCycleDefMetacode(p[1].nCycleID, p[1].nCycleSubID, "CYCL_DEF_", listArgs = p[3])

    def p_cycleDef_5(self, p):
        '''cycleDef : CYCLE_DEF_AXISLIST cycleKeyword cycleAxisList'''
        self.generateCycleDefMetacode(p[1].nCycleID, p[1].nCycleSubID, "CYCL_DEF_", listArgs = p[3])

    def p_cycleDef_6(self, p):
        '''cycleDef : CYCLE_DEF_VALUE cycleKeyword expression'''
        dictArgsNC = {}
        dictArgsNC["Value"] = p[3]
        self.generateCycleDefMetacode(p[1].nCycleID, p[1].nCycleSubID, "CYCL_DEF_",dictArgsNC)

    def p_cycleDef_14(self, p):
        '''cycleDef : CYCLE_DEF_VALUE word_cycleKeyword expression'''
        dictArgsNC = {}
        dictArgsNC["Value"] = p[3]
        self.generateCycleDefMetacode(p[1].nCycleID, p[1].nCycleSubID, "CYCL_DEF_",dictArgsNC)

    def p_cycleDef_7(self, p):
        '''cycleDef : CYCLE_DEF_VALUE_F cycleKeyword expression word'''
        dictArgsNC = {}
        dictArgsNC["Value"] = p[3]
        if p[4].pValue != None:
            dictArgsNC[p[4].pszName] = p[4].pValue

        self.generateCycleDefMetacode(p[1].nCycleID, p[1].nCycleSubID, "CYCL_DEF_", dictArgsNC)

    def p_cycleDef_8(self, p):
        '''cycleDef : CYCLE_DEF_PATH cycleKeyword path'''
        dictArgsNC = {}
        dictArgsNC["Value"] = self.CreateLiteralExprFromString(p[3])
        self.generateCycleDefMetacode(p[1].nCycleID, p[1].nCycleSubID, "CYCL_DEF_", dictArgsNC)
        
        
    def p_cycleDef_9(self, p):
        '''cycleDef : CYCLE_DEF_VARLIST cycleKeyword assignmentList'''
        self.generateCycleDefMetacode(p[1].nCycleID, p[1].nCycleSubID, "CYCL_DEF_")

    def p_cycleDef_10(self, p):
        '''cycleDef : TCH_PROBE tchKeywordList assignmentList'''
        self.generateCycleDefMetacode(p[1].nCycleID, p[1].nCycleSubID, "TCH_PROBE_")

    def p_cycleDef_10_PATH(self, p):
        '''cycleDef : TCH_PROBE_PATH assignmentList'''
        self.generateCycleDefMetacode(p[1].nCycleID, p[1].nCycleSubID, "TCH_PROBE_")

    def p_cycleDef_11(self, p):
        '''cycleDef : tchProbeArgumentList cycleArgumentList'''

        self.generateCycleDefMetacode(p[1].nCycleID, p[1].nCycleSubID, "TCH_PROBE_", p[2])

    def p_cycleDef_12(self, p):
        '''cycleDef : tchProbeVarAxisDir cycleKeyword VARIABLE AXIS direction'''
        dictArgsNC = {}
        dictArgsNC["Variable"] = self.CreateLiteralExprFromString(p[3])
        dictArgsNC["Axis"] = self.CreateLiteralExprFromString(p[4])
        dictArgsNC["Direction"] = self.CreateLiteralExprFromBool(p[5])
        self.generateCycleDefMetacode(p[1].nCycleID, p[1].nCycleSubID, "TCH_PROBE_", dictArgsNC)

    def p_cycleDef_13(self, p):
        '''cycleDef : TCH_PROBE_DATUMPLANE start_path_state tchKeywordList end_path_state tchProbeDatumPlaneArgumentList'''

        self.generateCycleDefMetacode(p[1].nCycleID, p[1].nCycleSubID, "TCH_PROBE_", p[5])

    def p_tchProbeDatumPlaneArgumentList_1(self, p):
        '''tchProbeDatumPlaneArgumentList : '''
        p[0] = {}

    def p_tchProbeDatumPlaneArgumentList_2(self, p):
        '''tchProbeDatumPlaneArgumentList : AXIS PROBE_ANGLE numExpression'''
        dictArgsNC = {}
        dictArgsNC["Axis"] = self.CreateLiteralExprFromString(p[1])
        dictArgsNC["Angle"] = p[3]
        p[0] = dictArgsNC

    def p_tchProbeDatumPlaneArgumentList_3(self, p):
        '''tchProbeDatumPlaneArgumentList : cycleArgumentList'''
        p[0] = p[1]

    def p_cycleKeyword_1(self, p):
        '''cycleKeyword : '''

    def p_cycleKeyword_2(self, p):
        '''cycleKeyword : CYCLE_KEYWORD'''

    def p_tchKeyword_1(self, p):
        '''tchKeyword : CYCLE_KEYWORD'''

    def p_tchKeyword_2(self, p):
        '''tchKeyword : STRING'''

    def p_tchKeywordList_1(self, p):
        '''tchKeywordList : '''

    def p_tchKeywordList_2(self, p):
        '''tchKeywordList : tchKeyword tchKeywordList'''

    def p_cycleDefArgumentList_1(self, p):
        '''cycleDefArgumentList : CYCLE_DEF_F'''
        p[0] = p[1]

    def p_cycleDefArgumentList_2(self, p):
        '''cycleDefArgumentList : CYCLE_DEF_F_DR'''
        p[0] = p[1]
        
    def p_cycleDefArgumentList_3(self, p):
        '''cycleDefArgumentList : CYCLE_DEF_F_DR_RADIUS'''
        p[0] = p[1]

    def p_cycleDefArgumentList_4(self, p):
        '''cycleDefArgumentList : CYCLE_DEF_T'''
        p[0] = p[1]

    def p_cycleDefArgumentList_5(self, p):
        '''cycleDefArgumentList : CYCLE_DEF_X'''
        p[0] = p[1]

    def p_cycleDefArgumentList_6(self, p):
        '''cycleDefArgumentList : CYCLE_DEF_Y'''
        p[0] = p[1]

    def p_cycleDefArgumentList_7(self, p):
        '''cycleDefArgumentList : CYCLE_DEF_X_Y_Z'''
        p[0] = p[1]

    def p_cycleDefArgumentList_8(self, p):
        '''cycleDefArgumentList : CYCLE_DEF_X_Y_CCX_CCY'''
        p[0] = p[1]

    def p_cycleDefArgumentList_9(self, p):
        '''cycleDefArgumentList : CYCLE_DEF_A_B_C'''
        p[0] = p[1]

    def p_cycleDefArgumentList_10(self, p):
        '''cycleDefArgumentList : CYCLE_DEF_AXIS_INCAXIS_HASH'''
        p[0] = p[1]

    def p_cycleDefArgumentList_11(self, p):
        '''cycleDefArgumentList : CYCLE_DEF_ROT_IROT'''
        p[0] = p[1]

    def p_tchProbeArgumentList_1(self, p):
        '''tchProbeArgumentList : TCH_PROBE_X_Y_Z'''
        p[0] = p[1]

    def p_tchProbeVarAxisDir_1(self, p):
        '''tchProbeVarAxisDir : TCH_PROBE_REFPLANE'''
        p[0] = p[1]

    def p_tchProbeVarAxisDir_2(self, p):
        '''tchProbeVarAxisDir : TCH_PROBE_X_Y_Z'''
        p[0] = p[1]

    def p_cycleArgumentList_1(self, p):
        '''cycleArgumentList : word'''
        dictArgsNC = {}
        if p[1].pValue != None:
            dictArgsNC[p[1].pszName] = p[1].pValue
        p[0] = dictArgsNC

    def p_cycleArgumentList_2(self, p):
        '''cycleArgumentList : cycleArgumentList word'''
        if p[2].pValue != None:
            (p[1])[p[2].pszName] = p[2].pValue

        p[0] = p[1]

    def p_cycleIndexList_1(self, p):
        '''cycleIndexList : intValue'''
        p[0] = []
        p[0].append(self.CreateLiteralExprFromInteger(p[1]))
        
    def p_cycleIndexList_2(self, p):
        '''cycleIndexList : cycleIndexList DIVIDE intValue'''
        p[0] = p[1]
        p[0].append(self.CreateLiteralExprFromInteger(p[3]))

    def p_cycleAxisList_1(self, p):
        '''cycleAxisList : '''
        p[0] = []

    def p_cycleAxisList_2(self, p):
        '''cycleAxisList : cycleAxisList AXIS'''
        p[0] = p[1]
        p[0].append(self.CreateLiteralExprFromString(p[2]))

    def p_cycleCall_1(self, p):
        '''cycleCall : CYCLE_CALL optionalM'''  
        self.callFactory.CreateMetacodeCall("CYCL_CALL")

    def p_word_cycleKeyword_1(self, p):
        '''word_cycleKeyword : ABST_OP'''  

    def p_optionalM_1(self, p):
        '''optionalM : '''

    def p_optionalM_2(self, p):
        '''optionalM : 'M' '''

    def p_optionalM_3(self, p):
        '''optionalM : mCode '''

    def p_assignmentList_1(self, p):
        '''assignmentList : assignment'''

    def p_assignmentList_2(self, p):
        '''assignmentList : assignment assignmentList'''

    def p_assignment_1(self, p):
        '''assignment : variable EQUALS expression'''
        self.callFactory.CreateAssignCall(p[1], p[3])

    def p_assignment_2(self, p):
        '''assignment : variable EQUALS autoExpr'''
        self.callFactory.CreateAssignCall(p[1], p[3])

    def p_autoExpr_1(self, p):
        '''autoExpr : AUTO'''
        p[0] = self.exprFactory.CreateMethodExpr("AUTO")

    def p_repeat_1(self, p):
        '''repeat : '''
        p[0] = 0

    def p_repeat_2(self, p):
        '''repeat : REP intValue'''
        p[0] = p[2]

    def p_repeat_3(self, p):
        '''repeat : REP intValue DIVIDE intValue'''
        if p[2] != p[4]:
            self.error = ""
            raise CseParseError

        p[0] = p[2]

    def p_calcFunc_1(self, p):
        '''calcFunc : FN0 assignment'''

    def p_calcFunc_2(self, p):
        '''calcFunc : FN1 variable EQUALS numExpression PLUS numExpression'''
        self.callFactory.CreateAssignCall(p[2], self.exprFactory.CreateBinaryArithmeticExpr(p[4], p[6], NCExpressionFactory.ADD_OP))
    
    def p_calcFunc_3(self, p):
        '''calcFunc : FN2 variable EQUALS numExpression MINUS numExpression'''
        self.callFactory.CreateAssignCall(p[2], self.exprFactory.CreateBinaryArithmeticExpr(p[4], p[6], NCExpressionFactory.SUB_OP))

    def p_calcFunc_4(self, p):
        '''calcFunc : FN3 variable EQUALS numExpression TIMES numExpression'''
        self.callFactory.CreateAssignCall(p[2], self.exprFactory.CreateBinaryArithmeticExpr(p[4], p[6], NCExpressionFactory.MULT_OP))

    def p_calcFunc_5(self, p):
        '''calcFunc : FN4 variable EQUALS numExpression TNC_DIV numExpression'''
        self.callFactory.CreateAssignCall(p[2], self.exprFactory.CreateBinaryArithmeticExpr(p[4], p[6], NCExpressionFactory.DIV_OP))

    def p_calcFunc_6(self, p):
        '''calcFunc : FN5 variable EQUALS UN_OP numExpression'''
        if p[4] != NCExpressionFactory.SQRT_OP:
            self.error = ""
            raise CseParseError

        self.callFactory.CreateAssignCall(p[2], self.exprFactory.CreateUnaryArithmeticExpr(p[5], NCExpressionFactory.SQRT_OP))

    def p_calcFunc_7(self, p):
        '''calcFunc : FN6 variable EQUALS UN_OP numExpression'''
        if p[4] != NCExpressionFactory.SIN_OP:
            self.error = ""
            raise CseParseError

        self.callFactory.CreateAssignCall(p[2], self.exprFactory.CreateUnaryArithmeticExpr(p[5], NCExpressionFactory.SIN_OP))

    def p_calcFunc_8(self, p):
        '''calcFunc : FN7 variable EQUALS UN_OP numExpression'''
        if p[4] != NCExpressionFactory.COS_OP:
            self.error = ""
            raise CseParseError

        self.callFactory.CreateAssignCall(p[2], self.exprFactory.CreateUnaryArithmeticExpr(p[5], NCExpressionFactory.COS_OP))

    def p_calcFunc_9(self, p):
        '''calcFunc : FN8 variable EQUALS numExpression LENGTH numExpression'''
        pSquare1Expr = self.exprFactory.CreateBinaryArithmeticExpr(p[4], p[4], NCExpressionFactory.MULT_OP)
        pSquare2Expr = self.exprFactory.CreateBinaryArithmeticExpr(p[6], p[6], NCExpressionFactory.MULT_OP)
        pSquareLengthExpr = self.exprFactory.CreateBinaryArithmeticExpr(pSquare1Expr, pSquare2Expr, NCExpressionFactory.ADD_OP)

        self.callFactory.CreateAssignCall(p[2], self.exprFactory.CreateUnaryArithmeticExpr(pSquareLengthExpr, NCExpressionFactory.SQRT_OP))

    def p_calcFunc_10(self, p):
        '''calcFunc : FN9 TNC_IF numExpression TNC_EQU numExpression TNC_GOTO labelExpr'''
        exprCondition = self.exprFactory.CreateBinaryArithmeticExpr(p[3], p[5], NCExpressionFactory.EQ_OP)
        self.callFactory.CreateIfCall(exprCondition, p[7], CallFactory.SEARCH_FORWARD_THEN_BACKWARD)

    def p_calcFunc_11(self, p):
        '''calcFunc : FN10 TNC_IF numExpression TNC_NE numExpression TNC_GOTO labelExpr'''
        self.callFactory.CreateIfCall(self.exprFactory.CreateBinaryArithmeticExpr(p[3], p[5], NCExpressionFactory.NE_OP), p[7], CallFactory.SEARCH_FORWARD_THEN_BACKWARD)

    def p_calcFunc_12(self, p):
        '''calcFunc : FN11 TNC_IF numExpression TNC_GT numExpression TNC_GOTO labelExpr'''
        self.callFactory.CreateIfCall(self.exprFactory.CreateBinaryArithmeticExpr(p[3], p[5], NCExpressionFactory.GT_OP), p[7], CallFactory.SEARCH_FORWARD_THEN_BACKWARD)

    def p_calcFunc_13(self, p):
        '''calcFunc : _embed0_calcFunc FN12  TNC_IF numExpression TNC_LT numExpression TNC_GOTO labelExpr'''
        self.callFactory.CreateIfCall(self.exprFactory.CreateBinaryArithmeticExpr(p[4], p[6], NCExpressionFactory.LT_OP), p[8], CallFactory.SEARCH_FORWARD_THEN_BACKWARD)

    def p__embed0_calcFunc(self, p):
        "_embed0_calcFunc :"
        if last_token.type != 'FN12':
            pass

        CseTNC_Lex.Core.g_nCurFunc = TNCFuncType.FUNC_FN_12

    def p_calcFunc_14(self, p):
        '''calcFunc : FN13 variable EQUALS numExpression ANGLE numExpression'''
        self.callFactory.CreateAssignCall(p[2], self.exprFactory.CreateBinaryArithmeticExpr(p[4], p[6], NCExpressionFactory.ATAN2_OP))

    def p_calcFunc_15(self, p):
        '''calcFunc : FN14 TNC_ERROR EQUALS intValue'''
        dictArgs = {}
        dictArgs["Value"] = self.CreateLiteralExprFromInteger(p[4])
        self.callFactory.CreateMetacodeCall("ERROR", dictArgs)

    def p_calcFunc_16(self, p):
        '''calcFunc : FN16 TNC_FPRINT TNC_FILE_PATH optionalFilePath'''

    def p_optionalFilePath_1(self, p):
        '''optionalFilePath : '''

    def p_optionalFilePath_2(self, p):
        '''optionalFilePath : TNC_FILE_PATH'''

    def p_calcFunc_17(self, p):
        '''calcFunc : FN17 TNC_SYSWRITE ID numExpression optionalNR optionalIDX EQUALS expression'''
        dictArgs = {}
        dictArgs["Identifier"] = p[4]

        if p[5] != None:
            dictArgs["Number"] = p[5]

        if p[6] != None:
            dictArgs["Index"] = p[6]

        dictArgs["Value"] = p[8]

        self.callFactory.CreateMetacodeCall("SYSWRITE", dictArgs)


    def p_calcFunc_18(self, p):
        '''calcFunc : FN18 TNC_SYSREAD VARIABLE EQUALS ID numExpression optionalNR optionalIDX'''
        dictArgs = {}
        dictArgs["Identifier"] = p[6]

        if p[7] != None:
            dictArgs["Number"] = p[7]

        if p[8] != None:
            dictArgs["Index"] = p[8]

        dictArgs["Variable"] = self.CreateLiteralExprFromString(p[3])

        self.callFactory.CreateMetacodeCall("SYSREAD", dictArgs)

    def p_calcFunc_19(self, p):
        '''calcFunc : FN19 TNC_PLC EQUALS plcExpr DIVIDE plcExpr'''
        dictArgs = {}
        dictArgs["Value1"] = p[4]
        dictArgs["Value2"] = p[6]
        self.callFactory.CreateMetacodeCall("PLC", dictArgs)

    def p_calcFunc_20(self, p):
        '''calcFunc : _embed1_calcFunc FN25 TNC_PRESET EQUALS AXIS DIVIDE numExpression DIVIDE numExpression'''
        dictArgs = {}
        dictArgs["JointName"] = self.CreateLiteralExprFromString(p[5])
        dictArgs["RefValue"] = p[7]
        dictArgs["TargetValue"] = p[9]

        self.callFactory.CreateMetacodeCall("PRESET", dictArgs)

    def p__embed1_calcFunc(self, p):
        "_embed1_calcFunc : "
        if last_token != 'FN25':
            pass

        CseTNC_Lex.Core.g_nCurFunc = TNCFuncType.FUNC_FN_25

    def p_calcFunc_21(self, p):
        '''calcFunc : FN26 TNC_TABOPEN STRING '''
        dictArgs = {}
        dictArgs["Path"] = self.CreateLiteralExprFromString(p[3])

        self.callFactory.CreateMetacodeCall("TABOPEN", dictArgs)

    def p_calcFunc_21_path(self, p):
        '''calcFunc : FN26 TNC_TABOPEN_PATH'''
        dictArgs = {}
        dictArgs["Path"] = self.CreateLiteralExprFromString(p[2])

        self.callFactory.CreateMetacodeCall("TABOPEN", dictArgs)

    def p_calcFunc_22(self, p):
        '''calcFunc : FN27 TNC_TABWRITE intValue DIVIDE path EQUALS VARIABLE'''
        dictArgs = {}
        dictArgs["Line"] = self.CreateLiteralExprFromInteger(p[3])
        dictArgs["Column"] = self.CreateLiteralExprFromString(p[5])
        dictArgs["Variable"] = self.CreateLiteralExprFromString(p[7])

        self.callFactory.CreateMetacodeCall("TABWRITE", dictArgs)

    def p_calcFunc_23(self, p):
        '''calcFunc : FN28 TNC_TABREAD VARIABLE EQUALS intValue DIVIDE path'''
        dictArgs = {}
        dictArgs["Variable"] = self.CreateLiteralExprFromString(p[3])
        dictArgs["Line"] = self.CreateLiteralExprFromInteger(p[5])
        dictArgs["Column"] = self.CreateLiteralExprFromString(p[7])

        self.callFactory.CreateMetacodeCall("TABREAD", dictArgs)

    def p_labelExpr_1(self, p):
        '''labelExpr : TNC_LABEL'''
        p[0] = self.CreateLiteralExprFromString(p[1])

    def p_labelExpr_2(self, p):
        '''labelExpr : TNC_LABEL_PREFIX numExpression'''
        pTargetExpr = self.exprFactory.CreateCastExpr(p[2], NCBasicType.INTEGER)
        p[0] = self.exprFactory.CreateBinaryArithmeticExpr(self.CreateLiteralExprFromString(p[1]), pTargetExpr, NCExpressionFactory.ADD_OP)

    def p_optionalNR_1(self, p):
        '''optionalNR : '''
        p[0] = None

    def p_optionalNR_2(self, p):
        '''optionalNR : NR numExpression'''
        p[0] = p[2]

    def p_optionalIDX_1(self, p):
        '''optionalIDX : '''
        p[0] = None

    def p_optionalIDX_2(self, p):
        '''optionalIDX : IDX numExpression'''
        p[0] = p[2]

    def p_plcExpr_1(self, p):
        '''plcExpr : floatValue'''
        p[0] = self.CreateLiteralExprFromDouble(p[1])

    def p_plcExpr_2(self, p):
        '''plcExpr : intValue'''
        p[0] = self.CreateLiteralExprFromInteger(p[1])

    def p_plcExpr_3(self, p):
        '''plcExpr : VARIABLE'''
        p[0] = self.exprFactory.CreateVariableExpr(p[1])

    def p_plcExpr_4(self, p):
        '''plcExpr : PLUS plcExpr'''
        p[0] = p[2]

    def p_plcExpr_5(self, p):
        '''plcExpr : MINUS plcExpr'''
        p[0] = self.exprFactory.CreateUnaryArithmeticExpr(p[2], NCExpressionFactory.NEG_OP)

    def p_planeCall_1(self, p):
        '''planeCall : PLANE_OP planeParams'''
        self.callFactory.CreateMetacodeCall("PLANE", p[2])

    def p_planeParams_1(self, p):
        '''planeParams : PLANE_RESET planeMoveReset'''
        p[0] = p[2]
        (p[0])["RESET"] = self.CreateLiteralExprFromBool(True)

    def p_planeParams_2(self, p):
        '''planeParams : PLANE_SPATIAL PLANE_SPA numExpression PLANE_SPB numExpression PLANE_SPC numExpression planeMove planeSeq planeRot'''
        p[0] = p[8]
        (p[0])["SPATIAL"] = self.CreateLiteralExprFromBool(True)
        (p[0])["SPA"] = p[3]
        (p[0])["SPB"] = p[5]
        (p[0])["SPC"] = p[7]

        if p[9].pValue != None:
            (p[0])[p[9].pszName] = p[9].pValue

        if p[10].pValue != None:
            (p[0])[p[10].pszName] = p[10].pValue

    def p_planeParams_3(self, p):
        '''planeParams : PLANE_RELATIV planeSPA planeSPB planeSPC planeMove planeSeq planeRot'''
        p[0] = p[5]
        (p[0])["RELATIV"] = self.CreateLiteralExprFromBool(True)
        
        if p[2] != None:
            (p[0])["SPA"] = p[2]
        
        if p[3] != None:
            (p[0])["SPB"] = p[3]
        
        if p[4] != None:
            (p[0])["SPC"] = p[4]
        
        if p[6].pValue != None:
            (p[0])[p[6].pszName] = p[6].pValue

        if p[7].pValue != None:
            (p[0])[p[7].pszName] = p[7].pValue

    def p_planeParams_4(self, p):
        '''planeParams : PLANE_VECTOR PLANE_BX numExpression PLANE_BY numExpression PLANE_BZ numExpression normalWord normalWord normalWord planeMove planeSeq planeRot'''
        p[0] = p[11]

        (p[0])["VECTOR"] = self.CreateLiteralExprFromBool(True)
        (p[0])["BX"] = p[3]
        (p[0])["BY"] = p[5]
        (p[0])["BZ"] = p[7]


        (p[0])[p[8].pszName] = p[8].pValue
        (p[0])[p[9].pszName] = p[9].pValue
        (p[0])[p[10].pszName] = p[10].pValue

        if p[12].pValue != None:
            (p[0])[p[12].pszName] = p[12].pValue
        if p[13].pValue != None:
            (p[0])[p[13].pszName] = p[13].pValue

    def p_planeParams_5(self, p):
        '''planeParams : _embed_planeParams_5 PLANE_AXIAL  planeABCList planeMove'''
        p[0] = p[4]

        (p[0])["AXIAL"] = self.CreateLiteralExprFromBool(True)

        for i in range(len(p[3])):
            word = (p[3])[i]
            (p[0])[word.pszName] = word.pValue

    def p__embed_planeParams_5(self, p):
        '''_embed_planeParams_5 : '''
        if last_token != 'PLANE_AXIAL':
            pass

        CseTNC_Lex.Core.g_nCurFunc = TNCFuncType.FUNC_PLANE_AXIAL

    def p_planeABCList_1(self, p):
        '''planeABCList : axisWord'''
        p[0] = []
        p[0].append(p[1])

    def p_planeABCList_2(self, p):
        '''planeABCList : planeABCList axisWord'''
        p[0] = p[1]
        p[0].append(p[2])

    def p_planeMoveReset_1(self, p):
        '''planeMoveReset : planeMove'''
        p[0] = p[1]

    def p_planeMoveReset_2(self, p):
        '''planeMoveReset : MB feedExpr'''
        p[0] = {}
        (p[0])["MB"] = p[2]

    def p_planeMove_1(self, p):
        '''planeMove : PLANE_MOVE optionalDistExpr optionalFeed'''
        p[0] = {}
        (p[0])["MOVE"] = self.CreateLiteralExprFromBool(True)

        if p[2] != None:
            (p[0])["ABST"] = p[2]
        if p[3] != None:
            (p[0])["F"] = p[3]

    def p_planeMove_2(self, p):
        '''planeMove : PLANE_STAY'''
        p[0] = {}
        (p[0])["STAY"] = self.CreateLiteralExprFromBool(True)


    def p_planeMove_3(self, p):
        '''planeMove : PLANE_TURN optionalMBExpr optionalFeed'''
        p[0] = {}
        (p[0])["TURN"] = self.CreateLiteralExprFromBool(True)

        if p[2] != None:
            (p[0])["MB"] = p[2]
        if p[3] != None:
            p[0]["F"] = p[3]

    def p_planeRot_1(self, p):
        '''planeRot : '''
        p[0] = TNCWordInfo()

    def p_planeRot_2(self, p):
        '''planeRot : PLANE_COORD_ROT'''
        p[0] = TNCWordInfo("COORD_ROT", self.CreateLiteralExprFromBool(True))

    def p_planeRot_3(self, p):
        '''planeRot : PLANE_TABLE_ROT'''
        p[0] = TNCWordInfo("TABLE_ROT", self.CreateLiteralExprFromBool(True))

    def p_planeSeq_1(self, p):
        '''planeSeq : '''
        p[0] = TNCWordInfo("", None)

    def p_planeSeq_2(self, p):
        '''planeSeq : PLANE_SEQ PLUS'''
        p[0] = TNCWordInfo("SEQ", self.CreateLiteralExprFromString("+"))

    def p_planeSeq_3(self, p):
        '''planeSeq : PLANE_SEQ MINUS'''
        p[0] = TNCWordInfo("SEQ", self.CreateLiteralExprFromString("-"))

    def p_optionalMBExpr_1(self, p):
        '''optionalMBExpr : '''
        p[0] = None

    def p_planeSPA_1(self, p):
        '''planeSPA : '''
        p[0] = None

    def p_planeSPA_2(self, p):
        '''planeSPA : PLANE_SPA numExpression'''
        p[0] = p[2]

    def p_planeSPB_1(self, p):
        '''planeSPB : '''
        p[0] = None

    def p_planeSPB_2(self, p):
        '''planeSPB : PLANE_SPB numExpression'''
        p[0] = p[2]

    def p_planeSPC_1(self, p):
        '''planeSPC : '''
        p[0] = None

    def p_planeSPC_2(self, p):
        '''planeSPC : PLANE_SPC numExpression'''
        p[0] = p[2]

    def p_optionalMBExpr_2(self, p):
        '''optionalMBExpr : MB feedExpr'''
        p[0] = p[2]

    def p_optionalDistExpr_1(self, p):
        '''optionalDistExpr : '''
        p[0] = None

    def p_optionalDistExpr_2(self, p):
        '''optionalDistExpr : ABST_OP numExpression'''
        p[0] = p[2]

    def p_SPLFunc_1(self, p):
        '''SPLFunc : SPL axisWordList kWordList optionalM optionalFeed'''
        if self.callFactory.IsMetacodeDefined("SPL"):
            dictArgsNC = {}
            for i in range(len(p[2])):
                word = (p[2])[i]
                dictArgsNC[word.pszName] = word.pValue
            for i in range(len(p[3])):
                word = (p[3])[i]
                dictArgsNC[word.pszName] = word.pValue
            if p[5] != None:
                dictArgsNC["F"] = p[5]
            self.callFactory.CreateMetacodeCall("SPL", dictArgsNC)

    def p_axisWordList_1(self, p):
        '''axisWordList : axisWord'''
        p[0] = []
        p[0].append(p[1])

    def p_axisWordList_2(self, p):
        '''axisWordList : axisWordList axisWord'''
        p[0] = p[1]
        p[0].append(p[2])
        
    def p_kWordList_1(self, p):
        '''kWordList : kWord kWord kWord'''
        p[0] = []
        p[0].append(p[1])
        p[0].append(p[2])
        p[0].append(p[3])
        
    def p_kWordList_2(self, p):
        '''kWordList : kWordList kWord kWord kWord '''
        p[0] = p[1]
        p[0].append(p[2])
        p[0].append(p[3])
        p[0].append(p[4])

    def p_kWord_1(self, p):
        '''kWord : kIndex axisWord'''
        p[0] = TNCWordInfo("", None)
        p[0].pszName = p[1] + p[2].pszName
        p[0].pValue = p[2].pValue

    def p_kIndex_1(self, p):
        '''kIndex : 'K' INTEGER_VALUE'''
        if p[2] == 1 or p[2] == 2 or p[2] == 3:
            p[0]= 'K' + str(p[2])
        else :
            self.error = ""
            raise CseParseError

    def p_declareSTR_1(self, p):
        '''declareSTR : DECLARE_OP STR_VARIABLE EQUALS STRING'''
        pExpr = self.CreateLiteralExprFromString(p[2])
        pInitExpr = self.CreateLiteralExprFromString(p[4])
        self.callFactory.CreateDeclareVariableCall(pExpr, NCBasicType.STRING, VariableManager.DEFAULT_MODE, pInitExpr)

    def p_variable_1(self, p):
        '''variable : VARIABLE'''
        p[0] = self.exprFactory.CreateVariableExpr(p[1])

    def p_variable_2(self, p):
        '''variable : STR_VARIABLE'''
        p[0] = self.exprFactory.CreateVariableExpr(p[1])

    def generateCycleDefMetacode(self, nID, nSubID, strPrefix, dictArgs = {}, listArgs = []):
        if nSubID != -1:
            dictArgs["ID"] = self.CreateLiteralExprFromInteger(nSubID)

        self.callFactory.CreateMetacodeCall(strPrefix+str(nID), dictArgs, listArgs)

    def parse(self, s):
        self.error = None
        CseTNC_Lex.Core.g_nCurFunc = CseTNC_Lex.TNCFuncType.FUNC_NONE
        self.parser.parse(s, tokenfunc = get_token)
        if self.error != None:
            return False

        # Lookahead: Check if the next line contains an RND command
        sNext = self.callFactory.PeekLine(1)
        if sNext == None:
            return True

        CseTNC_Lex.Core.g_nCurFunc = CseTNC_Lex.TNCFuncType.FUNC_NONE
        CseTNC_Lex.lex.input(sNext)

        while True:
            try:
                tok = CseTNC_Lex.lex.token()
            except CseParseError:
                # Parse errors in lookahead lines must be ignored here
                return True

            if not tok:
                return True

            if tok.type == "FUNC" and tok.value.nID == CseTNC_Lex.TNCFuncType.FUNC_RND:
                # Process RND line
                sNext = self.callFactory.GetNextLine()
                self.error = None
                CseTNC_Lex.Core.g_nCurFunc = CseTNC_Lex.TNCFuncType.FUNC_NONE
                self.parser.parse(sNext, tokenfunc = get_token)
                return self.error == None

class ParserExpr(ExprCore):

    g_pExpr = None

    start = 'startExpr'

    def p_startExpr(self, p):
        'startExpr : expression'
        ParserExpr.g_pExpr = p[1]

    def parse(self, s):
        self.error = None
        self.parser.parse(s)
        if self.error != None:
            return None
        
        return ParserExpr.g_pExpr

last_token = None

def get_token():
    global last_token
    last_token = CseTNC_Lex.lex.token()
    return last_token

if __name__ == '__main__':

    parser = Parser();
    while 1:
        try:
            s = input('GCode > ')
        except EOFError:
            break
        if not s: continue
        parser.error = None
        parser.parse(s)
        if parser.error != None:
            print("LOGIC ERROR")