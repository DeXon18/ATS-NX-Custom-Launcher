# -*- coding: utf-8 -*-
#
# History
#
# Date          Name                Description of Change
# 10-Jul-2013   Kevin Chen          Creation
# 06-Nov-2013   Jason Fu            Create rule for token programName and selectionName
# 20-Feb-2014   Jason Fu            Add a new token "SPL and a literal "K"
# 22-May-2014   Thomas Schulz       Add "WORK PLANE" for CYCLE DEF 19.0
# 18-Feb-2015   Thomas Schulz       Add "QR" and "QL" same as "Q" IR1128872
# 31-Mar-2016   Shuai Gao           Add new tokens "TNC_FILE_PATH", "TNC_FPRINT" and "FN16"
# 26-May-2016   Shuai Gao           Fix PR7723183
#                                   Add TNC Function Type "FUNC_BEGIN_PROGRAM", "FUNC_END_PROGRAM" and "FUNC_CALL_PROGRAM".
#                                   Update rules for tokens "BEGIN_PROGRAM", "END_PROGRAM" and "CALL_PGM".
#                                   Enhance the definition of "t_programName_path".
# 31-May-2016   Shuai Gao           Check whether the blank does exist before UNIT in "t_programName_path".
# 16-Jun-2016   Shuai Gao           PR7737853: Enhance rule for "CYCLE_KEYWORD" with "HSC-MODE"
# 25-Jul-2016   Shuai Gao           PR7761731: Add a new token "PLANE_RELATIV".
# 09-Aug-2016   Volker Grabowski    Use custom exception class to handle parse errors
# 02-Sep-2016   Volker Grabowski    Move CseParseError to CSEWrapper.py
# 01-Dec-2016   Shuai Gao           PR7881586: Enhance rule for "CYCLE_KEYWORD" with "EINLIPPEN-BOHREN".

import sys
import re
import os
import ply.lex as lex

class TNCFuncType:
    FUNC_NONE = 0
    FUNC_L = 1
    FUNC_LN = 2
    FUNC_LP = 3
    FUNC_LT = 4
    FUNC_LCT = 5
    FUNC_PCT = 6
    FUNC_CT = 7
    FUNC_CTP = 8
    FUNC_CHF = 9
    FUNC_CC = 10
    FUNC_C = 11
    FUNC_CP = 12
    FUNC_CR = 13
    FUNC_RND = 14
    FUNC_TCPM = 15
    FUNC_TCPM_RESET = 16
    FUNC_CYCLE_VOID = 17
    FUNC_CYCLE_VARLIST = 18
    FUNC_CYCLE_VALUE = 19
    FUNC_CYCLE_VALUE_F = 20
    FUNC_CYCLE_F = 21
    FUNC_CYCLE_F_DR = 22
    FUNC_CYCLE_F_DR_RADIUS = 23
    FUNC_CYCLE_T = 24
    FUNC_CYCLE_X = 25
    FUNC_CYCLE_Y = 26
    FUNC_CYCLE_X_Y_Z = 27
    FUNC_CYCLE_X_Y_CCX_CCY = 28
    FUNC_CYCLE_A_B_C = 29
    FUNC_CYCLE_AXIS_INCAXIS_HASH = 30
    FUNC_CYCLE_ROT_IROT = 31
    FUNC_CYCLE_PATH = 32
    FUNC_CYCLE_AXISLIST = 33
    FUNC_CYCLE_INDEXLIST = 34
    FUNC_CYCLE_REFPLANE = 35
    FUNC_CYCLE_DATUMPLANE = 36
    FUNC_FN_12 = 37
    FUNC_FN_25 = 38
    FUNC_PLANE_AXIAL = 39
    FUNC_BEGIN_PROGRAM = 40
    FUNC_END_PROGRAM = 41
    FUNC_CALL_PROGRAM = 42
    
class TNCFuncInfo:

    def __init__(self, funcType, funcName):
        self.nID = funcType
        self.pszName = funcName

class TNCCycleInfo:

    def __init__(self, cycleID, cycleSubID, funcType):
        self.nCycleID = cycleID
        self.nCycleSubID = cycleSubID
        self.nFuncID = funcType

class TNCWordInfo:

    def __init__(self, name = "", expression = None):
        self.pszName = name
        self.pValue = expression

class Core():
    g_nCurFunc = TNCFuncType.FUNC_NONE
    runInConsole = 0
    Debug = 0

if Core.runInConsole == 0:
    from CSEWrapper import CseParseError
    from CSEWrapper import NCExpressionFactory

if Core.Debug == 1:
    fileLog = open(os.path.split(os.path.realpath(__file__))[0] + r'\log.txt','a')
    logger = lex.PlyLogger(fileLog)

# Get the token map
tokens = ( 
    'FLOAT_VALUE', 'INTEGER_VALUE', 'COMMENT', 'BEGIN_PROGRAM', 'END_PROGRAM', 'UNIT', 'BLK_FORM', 'STOP', 'VARIABLE',
    'FUNC','FUNC_APPR_DEP', 'FUNC_ARG','TOOL_DEF', 'TOOL_CALL',
    'CYCLE_DEF_VARLIST', 'CYCLE_DEF_VOID', 'CYCLE_DEF_VALUE','CYCLE_DEF_VALUE_F', 'CYCLE_DEF_F', 'CYCLE_DEF_F_DR', 'CYCLE_DEF_F_DR_RADIUS', 'CYCLE_DEF_T',
    'CYCLE_DEF_X', 'CYCLE_DEF_Y', 'CYCLE_DEF_X_Y_Z', 'CYCLE_DEF_X_Y_CCX_CCY', 'CYCLE_DEF_A_B_C', 'CYCLE_DEF_AXIS_INCAXIS_HASH',
    'CYCLE_DEF_AXISLIST', 'CYCLE_DEF_ROT_IROT', 'CYCLE_DEF_PATH', 'CYCLE_DEF_INDEXLIST',
    'TCH_PROBE', 'TCH_PROBE_REFPLANE', 'TCH_PROBE_X_Y_Z', 'TCH_PROBE_DATUMPLANE',
    'SEL_TABLE', 'CYCLE_CALL', 'CYCLE_KEYWORD',
    'FN0', 'FN1', 'FN2', 'FN3', 'FN4', 'FN5', 'FN6', 'FN7', 'FN8', 'FN9', 'FN10', 'FN11', 'FN12', 'FN13', 'FN14', 'FN16', 'FN17', 'FN18', 'FN19', 'FN25', 'FN26', 'FN27', 'FN28',
    'TNC_ERROR', 'TNC_PLC', 'TNC_PRESET', 'TNC_FILE_PATH', 'TNC_FPRINT', 'TNC_SYSREAD', 'TNC_SYSWRITE', 'TNC_TABOPEN','TNC_TABWRITE', 'TNC_TABREAD',
    'ID', 'NR', 'IDX',
    'MFUNC', 'AXIS', 'INC_AXIS', 'NORMAL', 'TOOLDIR', 'F_PARAM', 'AXIS_PARAM', 'PATHCTRL_PARAM',
    'CCX_WORD','CCY_WORD', 'ROT_WORD', 'IROT_WORD', 'FEED', 'MB', 'TNC_MAX', 'AUTO', 'R_WORD', 'RADIUS_WORD', 'TNC_SPINDLE', 'T_WORD', 'HASH_WORD',
    'RADIUS_CORR', 'ANGLE', 'PROBE_ANGLE', 'LENGTH', 'CENTER_ANGLE', 'ROT_DIR', 'POLAR_RADIUS', 'POLAR_ANGLE', 'INC_POLAR_ANGLE', 'LOOKAHEAD', 'REP',
    'PLANE_OP', 'PLANE_RESET', 'PLANE_SPATIAL', 'PLANE_RELATIV', 'PLANE_AXIAL', 'PLANE_VECTOR', 'PLANE_SPA', 'PLANE_SPB', 'PLANE_SPC', 'PLANE_BX', 'PLANE_BY', 'PLANE_BZ', 'PLANE_MOVE', 'PLANE_STAY', 'PLANE_TURN', 'PLANE_COORD_ROT', 'PLANE_TABLE_ROT', 'PLANE_SEQ',
    'TNC_LABEL_PREFIX', 'TNC_LABEL', 'CALL', 'CALL_PGM',
    'TNC_PI', 'TNC_IF', 'TNC_GOTO', 'TNC_DIV', 'TNC_EQU', 'TNC_NE', 'TNC_GT', 'TNC_LT',
    'UN_OP', 'FRAC_OP', 'PATH', 'STRING', 'EOL', 'DECLARE_OP', 'STR_VARIABLE',
    'QS_CHAINLINK_OP', 'TOCHAR_OP', 'SUBSTR_OP', 'TONUMB_OP', 'STRLEN_OP','STRCOMP_OP', 'INSTR_OP', 'ABST_OP',
    'DAT', 'DECIMALS', 'SRC', 'SEA', 'BEG',
    'EQUALS', 'PLUS', 'MINUS', 'TIMES', 'POWER', 'DIVIDE',
    'TCH_PROBE_PATH', 'TNC_TABOPEN_PATH', 'SPL'
    )

literals = ['M', 'N','G','R','K','(',')']

t_EQUALS  = r'='
t_PLUS    = r'\+'
t_MINUS   = r'-'
t_TIMES   = r'\*'
t_POWER   = r'\^'
t_DIVIDE  = r'/'
t_ignore  = " \t"

# Declare the state
states = (  ('path','exclusive'), 
            ('programName','exclusive'), 
            ('selectionName','exclusive'), )

def t_TNC_IF (t):
    r'IF'
    return t

def t_TNC_GOTO (t):
    r'GOTO'
    return t

def t_TNC_DIV (t):
    r'DIV'
    return t

def t_TNC_EQU (t):
    r'EQU'
    return t

def t_TNC_GT (t):
    r'GT'
    return t

def t_TNC_ERROR (t):
    r'ERROR'
    return t

def t_TNC_PLC (t):
    r'PLC'
    return t

def t_TNC_PRESET (t):
    r'PRESET'
    return t

def t_TNC_FPRINT (t):
    r'F-PRINT'
    return t

def t_TNC_FILE_PATH (t):
    r'TNC:\\+[a-zA-Z0-9_-]([a-zA-Z0-9_-]|[:\/\\\.,])*'
    return t

def t_TNC_SYSREAD (t):
    r'SYSREAD'
    return t

def t_TNC_SYSWRITE (t):
    r'SYSWRITE'
    return t

def t_TNC_TABOPEN_PATH (t):
    r'TABOPEN[ \t]+[a-zA-Z0-9_-]([a-zA-Z0-9_-]|[:\/\\\.,])*'
    return t

def t_TNC_TABOPEN (t):
    r'TABOPEN'
    return t

def t_TNC_TABWRITE (t):
    r'TABWRITE'
    return t

def t_TNC_TABREAD (t):
    r'TABREAD'
    return t

def t_NR (t):
    r'NR'
    return t

def t_IDX (t):
    r'IDX'
    return t

def t_CCX_WORD (t):
    r'CCX'
    return t

def t_CCY_WORD (t):
    r'CCY'
    return t

def t_IROT_WORD (t):
    r'IROT'
    return t

def t_MB (t):
    r'MB'
    return t

def t_TNC_MAX (t):
    r'MAX'
    return t

def t_AUTO (t):
    r'AUTO'
    return t

def t_HASH_WORD (t):
    r'\#'
    return t

def t_RADIUS_CORR (t):
    r'(RL)|(RR)'
    return t

def t_PROBE_ANGLE (t):
    r'(ANGLE:)|(WINKEL:)'
    return t

def t_PLANE_RESET (t):
    r'RESET'
    return t

def t_PLANE_SPATIAL (t):
    r'SPATIAL'
    return t

def t_PLANE_RELATIV (t):
    r'RELATIV'
    return t

def t_PLANE_SPA (t):
    r'SPA'
    return t

def t_PLANE_SPB (t):
    r'SPB'
    return t

def t_PLANE_SPC (t):
    r'SPC'
    return t

def t_PLANE_VECTOR (t):
    r'VECTOR'
    return t

def t_PLANE_BX (t):
    r'BX'
    return t

def t_PLANE_BY (t):
    r'BY'
    return t

def t_PLANE_BZ (t):
    r'BZ'
    return t

def t_PLANE_MOVE (t):
    r'MOVE'
    return t

def t_PLANE_STAY (t):
    r'STAY'
    return t

def t_PLANE_TURN (t):
    r'TURN'
    return t

def t_PLANE_COORD_ROT (t):
    r'COORD[ \t]+ROT'
    return t

def t_PLANE_TABLE_ROT (t):
    r'TABLE[ \t]+ROT'
    return t

def t_PLANE_SEQ (t):
    r'SEQ'
    return t

def t_FRAC_OP (t):
    r'FRAC'
    return t

def t_QS_CHAINLINK_OP (t):
    r'\|\|'
    return t

def t_TOCHAR_OP (t):
    r'TOCHAR'
    return t

def t_SUBSTR_OP (t):
    r'SUBSTR'
    return t

def t_TONUMB_OP (t):
    r'TONUMB'
    return t

def t_STRLEN_OP (t):
    r'STRLEN'
    return t

def t_STRCOMP_OP (t):
    r'STRCOMP'
    return t

def t_INSTR_OP (t):
    r'INSTR'
    return t

def t_DAT (t):
    r'DAT\+'
    return t

def t_CALL_PGM (t):
    r'CALL[ \t]+PGM[ \t]*'
    Core.g_nCurFunc = TNCFuncType.FUNC_CALL_PROGRAM
    return t

def t_TOOL_DEF (t):
    r'TOOL[ \t]+DEF'
    return t

def t_TOOL_CALL (t):
    r'TOOL[ \t]+CALL'
    return t

def t_SEL_TABLE (t):
    r'SEL[ \t]+TABLE[ \t]*'
    return t

def t_STOP (t):
    r'STOP'
    return t

def t_VARIABLE (t):
    r'(Q|QR|QL)\d+'
    return t

def t_STR_VARIABLE (t):
    r'QS\d+'
    return t

def t_DECLARE_OP (t):
    r'DECLARE[ \t]STRING'
    return t

def t_BEGIN_PROGRAM (t):
    r'BEGIN[ \t]PGM[ \t]*'
    Core.g_nCurFunc = TNCFuncType.FUNC_BEGIN_PROGRAM
    return t

def t_END_PROGRAM (t):
    r'END[ \t]PGM[ \t]*'
    Core.g_nCurFunc = TNCFuncType.FUNC_END_PROGRAM
    return t

def t_BLK_FORM (t):
    r'BLK[ \t]FORM'
    return t

def t_CYCLE_CALL (t):
    r'CYCL[ \t]+CALL'
    return t

def t_MFUNC (t):
    'M\d+'
    return t

def t_COMMENT_1(t):
    r';(.)*'
    t.type = 'COMMENT'
    return t

def t_COMMENT_2(t):
    r'\*[ \t]*-(.)*'
    t.type = 'COMMENT'
    return t

def t_FUNC_2(t):
    r'LN'
    t.value = TNCFuncInfo(TNCFuncType.FUNC_LN, t.value)
    t.type = "FUNC"
    return t

def t_FUNC_3(t):
    r'LP'
    t.value = TNCFuncInfo(TNCFuncType.FUNC_LP, t.value)
    t.type = "FUNC"
    return t

def t_FUNC_4(t):
    r'LT'
    if Core.g_nCurFunc == TNCFuncType.FUNC_FN_12:
        t.type = 'TNC_LT'
        return t
    else:
        t.value = TNCFuncInfo(TNCFuncType.FUNC_LT, t.value)
        t.type = "FUNC"
        return t

def t_FUNC_6(t):
    r'CTP'
    t.value = TNCFuncInfo(TNCFuncType.FUNC_CTP, t.value)
    t.type = "FUNC"
    return t

def t_FUNC_5(t):
    r'CT'
    t.value = TNCFuncInfo(TNCFuncType.FUNC_CT, t.value)
    t.type = "FUNC"
    return t

def t_FUNC_7(t):
    r'LCT'
    t.value = TNCFuncInfo(TNCFuncType.FUNC_LCT, t.value)
    t.type = "FUNC"
    return t

def t_FUNC_8(t):
    r'PCT'
    t.value = TNCFuncInfo(TNCFuncType.FUNC_PCT, t.value)
    t.type = "FUNC"
    return t

def t_FUNC_9(t):
    r'CP'
    t.value = TNCFuncInfo(TNCFuncType.FUNC_CP, t.value)
    t.type = "FUNC"
    return t

def t_FUNC_10(t):
    r'CR'
    t.value = TNCFuncInfo(TNCFuncType.FUNC_CR, t.value)
    t.type = "FUNC"
    return t
    
def t_SPL(t):
    r'SPL'
    return t
    
def t_CYCLE_DEF_VARLIST_2(t):
    r'CYCL[ \t]+DEF[ \t]*(20\.0|21\.0|22\.0|23\.0|24\.0|25\.0|27\.0|28\.0)'
    t.type = "CYCLE_DEF_VARLIST"
    t.value = TNCCycleInfo(determineNewCycleID(t.value), -1, TNCFuncType.FUNC_CYCLE_VARLIST)
    Core.g_nCurFunc = TNCFuncType.FUNC_CYCLE_VARLIST
    return t

def t_CYCLE_DEF_VOID(t):
    r'CYCL[ \t]+DEF[ \t]*(1\.0|2\.0|3\.0|4\.0|5\.0|7\.0|8\.0|9\.0|10\.0|11\.0|12\.0|13\.0|14\.0|17\.0|18\.0|19\.0|26\.0|30\.0|30.1)'
    nCycleID, nCycleSubID = determineOldCycleIDs(t.value)
    t.value = TNCCycleInfo(nCycleID, nCycleSubID, TNCFuncType.FUNC_CYCLE_VOID)
    Core.g_nCurFunc = TNCFuncType.FUNC_CYCLE_VOID
    return t

def t_CYCLE_DEF_VALUE(t):
    r'CYCL[ \t]+DEF[ \t]*(1\.[1-4]|2\.[1-3]|3\.[1-2]|4\.[1-2]|5\.[124]|9\.[1-9]|11\.[1-9]|13\.[1-9]|17\.[1-9]|18\.[1-9]|30\.4)'
    nCycleID, nCycleSubID = determineOldCycleIDs(t.value)
    t.value = TNCCycleInfo(nCycleID, nCycleSubID, TNCFuncType.FUNC_CYCLE_VALUE)
    Core.g_nCurFunc = TNCFuncType.FUNC_CYCLE_VALUE
    return t

def t_CYCLE_DEF_VALUE_F(t):
    r'CYCL[ \t]+DEF[ \t]*(3\.3|4\.3|5\.3|30\.5)'
    nCycleID, nCycleSubID = determineOldCycleIDs(t.value)
    t.value = TNCCycleInfo(nCycleID, nCycleSubID, TNCFuncType.FUNC_CYCLE_F_DR)
    Core.g_nCurFunc = TNCFuncType.FUNC_CYCLE_VALUE_F
    return t

def t_CYCLE_DEF_F(t):
    r'CYCL[ \t]+DEF[ \t]*(1\.5|2\.4|3\.6|30\.6)'
    nCycleID, nCycleSubID = determineOldCycleIDs(t.value)
    t.value = TNCCycleInfo(nCycleID, nCycleSubID, TNCFuncType.FUNC_CYCLE_F)
    Core.g_nCurFunc = TNCFuncType.FUNC_CYCLE_F
    return t

def t_CYCLE_DEF_F_DR(t):
    r'CYCL[ \t]+DEF[ \t]*5\.5'
    nCycleID, nCycleSubID = determineOldCycleIDs(t.value)
    t.value = TNCCycleInfo(nCycleID, nCycleSubID, TNCFuncType.FUNC_CYCLE_F_DR)
    Core.g_nCurFunc = TNCFuncType.FUNC_CYCLE_F_DR
    return t

def t_CYCLE_DEF_F_DR_RADIUS(t):
    r'CYCL[ \t]+DEF[ \t]*4\.6'
    nCycleID, nCycleSubID = determineOldCycleIDs(t.value)
    t.value = TNCCycleInfo(nCycleID, nCycleSubID, TNCFuncType.FUNC_CYCLE_F_DR_RADIUS)
    Core.g_nCurFunc = TNCFuncType.FUNC_CYCLE_F_DR_RADIUS
    return t

def t_CYCLE_DEF_X(t):
    r'CYCL[ \t]+DEF[ \t]*(3\.4|4\.4)'
    nCycleID, nCycleSubID = determineOldCycleIDs(t.value)
    t.value = TNCCycleInfo(nCycleID, nCycleSubID, TNCFuncType.FUNC_CYCLE_X)
    Core.g_nCurFunc = TNCFuncType.FUNC_CYCLE_X
    return t

def t_CYCLE_DEF_Y(t):
    r'CYCL[ \t]+DEF[ \t]*(3\.5|4\.5)'
    nCycleID, nCycleSubID = determineOldCycleIDs(t.value)
    t.value = TNCCycleInfo(nCycleID, nCycleSubID, TNCFuncType.FUNC_CYCLE_Y)
    Core.g_nCurFunc = TNCFuncType.FUNC_CYCLE_Y
    return t

def t_CYCLE_DEF_AXIS_INCAXIS_HASH(t):
    r'CYCL[ \t]+DEF[ \t]*7\.[1-9]'
    nCycleID, nCycleSubID = determineOldCycleIDs(t.value)
    t.value = TNCCycleInfo(nCycleID, nCycleSubID, TNCFuncType.FUNC_CYCLE_AXIS_INCAXIS_HASH)
    Core.g_nCurFunc = TNCFuncType.FUNC_CYCLE_AXIS_INCAXIS_HASH
    return t

def t_CYCLE_DEF_AXISLIST(t):
    r'CYCL[ \t]+DEF[ \t]*8\.[1-9]'
    nCycleID, nCycleSubID = determineOldCycleIDs(t.value)
    t.value = TNCCycleInfo(nCycleID, nCycleSubID, TNCFuncType.FUNC_CYCLE_AXISLIST)
    Core.g_nCurFunc = TNCFuncType.FUNC_CYCLE_AXISLIST
    return t

def t_CYCLE_DEF_ROT_IROT(t):
    r'CYCL[ \t]+DEF[ \t]*10\.[1-9]'
    nCycleID, nCycleSubID = determineOldCycleIDs(t.value)
    t.value = TNCCycleInfo(nCycleID, nCycleSubID, TNCFuncType.FUNC_CYCLE_ROT_IROT)
    Core.g_nCurFunc = TNCFuncType.FUNC_CYCLE_ROT_IROT
    return t

def t_CYCLE_DEF_PATH(t):
    r'CYCL[ \t]+DEF[ \t]*12\.[1-9]'
    nCycleID, nCycleSubID = determineOldCycleIDs(t.value)
    t.value = TNCCycleInfo(nCycleID, nCycleSubID, TNCFuncType.FUNC_CYCLE_PATH)
    Core.g_nCurFunc = TNCFuncType.FUNC_CYCLE_PATH
    return t

def t_CYCLE_DEF_INDEXLIST(t):
    r'CYCL[ \t]+DEF[ \t]*14\.[1-9]'
    nCycleID, nCycleSubID = determineOldCycleIDs(t.value)
    t.value = TNCCycleInfo(nCycleID, nCycleSubID, TNCFuncType.FUNC_CYCLE_INDEXLIST)
    Core.g_nCurFunc = TNCFuncType.FUNC_CYCLE_INDEXLIST
    return t

def t_CYCLE_DEF_A_B_C(t):
    r'CYCL[ \t]+DEF[ \t]*19\.[1-9]'
    nCycleID, nCycleSubID = determineOldCycleIDs(t.value)
    t.value = TNCCycleInfo(nCycleID, nCycleSubID, TNCFuncType.FUNC_CYCLE_A_B_C)
    Core.g_nCurFunc = TNCFuncType.FUNC_CYCLE_A_B_C
    return t

def t_CYCLE_DEF_X_Y_CCX_CCY(t):
    r'CYCL[ \t]+DEF[ \t]*26.[1-9]'
    nCycleID, nCycleSubID = determineOldCycleIDs(t.value)
    t.value = TNCCycleInfo(nCycleID, nCycleSubID, TNCFuncType.FUNC_CYCLE_X_Y_CCX_CCY)
    Core.g_nCurFunc = TNCFuncType.FUNC_CYCLE_X_Y_CCX_CCY
    return t

def t_CYCLE_DEF_X_Y_Z(t):
    r'CYCL[ \t]+DEF[ \t]*30\.[2-3]'
    nCycleID, nCycleSubID = determineOldCycleIDs(t.value)
    t.value = TNCCycleInfo(nCycleID, nCycleSubID, TNCFuncType.FUNC_CYCLE_X_Y_Z)
    Core.g_nCurFunc = TNCFuncType.FUNC_CYCLE_X_Y_Z
    return t

def t_CYCLE_DEF_T(t):
    r'CYCL[ \t]+DEF[ \t]*32\.\d'
    nCycleID, nCycleSubID = determineOldCycleIDs(t.value)
    t.value = TNCCycleInfo(nCycleID, nCycleSubID, TNCFuncType.FUNC_CYCLE_T)
    Core.g_nCurFunc = TNCFuncType.FUNC_CYCLE_T
    return t

def t_CYCLE_DEF_VARLIST_1(t):
    r'CYCL[ \t]+DEF[ \t]*\d+'
    t.value = TNCCycleInfo(determineNewCycleID(t.value), -1, TNCFuncType.FUNC_CYCLE_VARLIST)
    Core.g_nCurFunc = TNCFuncType.FUNC_CYCLE_VARLIST
    t.type = "CYCLE_DEF_VARLIST"
    return t


def t_TCH_PROBE_REFPLANE(t):
    r'TCH[ \t]+PROBE[ \t]*0\.0'
    nCycleID, nCycleSubID = determineOldCycleIDs(t.value)
    t.value = TNCCycleInfo(nCycleID, nCycleSubID, TNCFuncType.FUNC_CYCLE_REFPLANE)
    Core.g_nCurFunc = TNCFuncType.FUNC_CYCLE_REFPLANE
    return t

def t_TCH_PROBE_X_Y_Z(t):
    r'TCH[ \t]+PROBE[ \t]*0\.1'
    nCycleID, nCycleSubID = determineOldCycleIDs(t.value)
    t.value = TNCCycleInfo(nCycleID, nCycleSubID, TNCFuncType.FUNC_CYCLE_X_Y_Z)
    Core.g_nCurFunc = TNCFuncType.FUNC_CYCLE_X_Y_Z
    return t

def t_TCH_PROBE_DATUMPLANE(t):
    r'TCH[ \t]+PROBE[ \t]*1\.[\d]+'
    nCycleID, nCycleSubID = determineOldCycleIDs(t.value)
    t.value = TNCCycleInfo(nCycleID, nCycleSubID, TNCFuncType.FUNC_CYCLE_DATUMPLANE)
    Core.g_nCurFunc = TNCFuncType.FUNC_CYCLE_DATUMPLANE
    return t

def t_TCH_PROBE_PATH(t):
    r'TCH[ \t]+PROBE[ \t]*[\d]+([ \t]+[a-zA-Z0-9_-]([a-zA-Z0-9_-]|[:\/\\\.,])*)+'
    m = re.search('[ \t]+Q\d+$', t.value)
    if m.group() != None:
        t.lexer.lexpos -= len(m.group())

    m = re.search('TCH[ \t]+PROBE[ \t]*[\d]+', t.value)
    nCycleID = determineNewCycleID(m.group())
    t.value = TNCCycleInfo(nCycleID, -1, TNCFuncType.FUNC_CYCLE_REFPLANE)
    Core.g_nCurFunc = TNCFuncType.FUNC_CYCLE_REFPLANE
    return t

def t_TCH_PROBE(t):
    r'TCH[ \t]+PROBE[ \t]*[\d]+'
    nCycleID = determineNewCycleID(t.value)
    t.value = TNCCycleInfo(nCycleID, -1, TNCFuncType.FUNC_CYCLE_VARLIST)
    Core.g_nCurFunc = TNCFuncType.FUNC_CYCLE_VARLIST
    return t

def t_CYCLE_KEYWORD_1(t):
    r'(PRESS[ ]IN[ ]BAR)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_2(t):
    r'(PLAN[ ]DE[ ]REFERENCE)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_3(t):
    r'(SELECT[ ]KINEMATIC)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_4(t):
    r'(MACHINE[ ]CYCLE)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_5(t):
    r'(ATC)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_6(t):
    r'(VRTANI[ ]ZAVITU[ ]NOVE)|(REZANI[ ]VNITRNIHO[ ]ZAVITU[ ]GS[ ]NOVE)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_7(t):
    r'(UNIVERSAL[ ]VRTANI)|(UNIVERSAL[ ]HLOUBKOVE[ ]VRTANI)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_9(t):
    r'(STOUP)|(REZANI[ ]ZAVITU)|(ROVINA[ ]OBRABENÍ)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_10(t):
    r'(VRTANI[ ]ZAVITU)|(NULOVY[ ]BOD)|(REZANI[ ]VNITRNIHO[ ]ZAVITU[ ]GS)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_11(t):
    r'(HLUBOKE[ ]VRTANI)|(VZDAL)|(HLOUBKA)|(PRISUV)|(PRODL.)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_12(t):
    r'(BUITENSCHROEFDR.[ ]FR.)|(GEGEVENS[ ]AANEENGESLOTEN[ ]CONTOUR)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_13(t):
    r'(SCHROEFDRAAD[ ]FREZEN[ ]MET[ ]VERZINKEN[ ]EN[ ]VOORBOREN)|(HELIX-SCHROEFDRAAD[ ]FREZEN[ ]MET[ ]VERZINKEN)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_17(t):
    r'(AFFREZEN)|(LINEAIR[ ]AFVLAKKEN)|(VLAKFREZEN)|(CENTREREN)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_18(t):
    r'(PATROON[ ]OP[ ]CIRKEL)|(PATROON[ ]OP[ ]LIJNEN)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_19(t):
    r'(KAMER[ ]NABEWERKEN)|(TAP[ ]NABEWERKEN)|(RONDK.[ ]NABEWERKEN)|(RONDE[ ]TAP[ ]NABEWERKEN)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_15(t):
    r'(RONDE[ ]SLEUF)|(RECHTHOEKIGE[ ]TAP)|(RONDE[ ]TAP)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_20(t):
    r'(SLEUF[ ]PENDELEND)|(RONDE[ ]SLEUF)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_21(t):
    r'(SCHROEFDRAAD[ ]TAPPEN[ ]NIEUW)|(SCHR.[ ]TAPPEN[ ]GS[ ]NIEUW)|(BOORFREZEN)|(SCHR.[ ]TAPPEN[ ]SPAANBR.)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_22(t):
    r'(IN[ ]VRIJLOOP[ ]VERPLAATSEN)|(UNIVERSEEL-DIEFBOREN)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_23(t):
    r'(CILINDERMANTEL[ ]CONTOUR)|(BOREN)|(UITDRAAIEN)|(UNIVERSEELBOREN)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_24(t):
    r'(CILINDERMANTEL[ ]DAM)|(CILINDERMANTEL)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_25(t):
    r'(AANEENGESLOTEN[ ]CONTOUR)|(MAATFACTOR[ ]ASSPEC.)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_26(t):
    r'(NABEWERKEN[ ]DIEPTE)|(NABEWERKEN[ ]ZIJKANT)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_27(t):
    r'(BEWERKINGSVLAK)|(CONTOURGEGEVENS)|(VOORBOREN)|(RUIMEN)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_28(t):
    r'(SCHR.-TAPPEN[ ]GS)|(SPOED)|(DRAADSNIJDEN)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_29(t):
    r'CONTOURLABEL'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_30(t):
    r'(ROTATIE)|(MAATFACTOR)|(ORIËNTATIE)|(HOEK)|(ROT[ ]UEBER[ ]DREHACHSE)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_31(t):
    r'(STILSTANDTIJD)|(ST.TIJD)|(S.TIJD)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_32(t):
    r'(KAMERFREZEN)|(RONDKAMER.)|(RADIUS)|(NULPUNT)|(SPIEGELEN)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_33(t):
    r'(SCHROEFDRAADTAPPEN)|(SLEUFFREZEN)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_34(t):
    r'(DIEPBOREN.)|(AFST)|(DIEPTE)|(ZUSTLG)|(VERPL.)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_35(t):
    r'(DADOS[ ]DO[ ]TRAÇADO[ ]DO[ ]CONTORNO)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_36(t):
    r'(FRESAR[ ]REBAIXAMENTO[ ]EN[ ]ROSCA)|(FRESAR[ ]ROSCA[ ]DE[ ]HÉLICE)|(FR.[ ]ROSCA[ ]EXTERIOR)|(FRESAR[ ]ROSCA)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_37(t):
    r'(ILHAS[ ]RECTANGULARES)|(ILHAS[ ]CIRCULARES)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_38(t):
    r'(FRESAR[ ]RANHURA)|(RANHURA[ ]CIRCULAR)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_39(t):
    r'(CENTRAR)|(MEMORIZAÇÃO[ ]PONTO[ ]REFERÊNCIA)|(CAIXA[ ]RECTANGULAR)|(CAIXA[ ]CIRCULAR\.)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_40(t):
    r'(FIGURA[ ]CÍRCULO)|(FIGURA[ ]LINHAS)|(FACEJAR)|(SUPERFÍCIE[ ]REGULAR)|(FRESA[ ]PLANA)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_41(t):
    r'(ACABAMENTO[ ]DA[ ]CAIXA)|(ACABAMENTO[ ]DA[ ]ILHA)|(CAIXA[ ]CIRC.[ ]ACABAMENTO)|(ILHA[ ]CIRC.[ ]ACABAMENTO)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_42(t):
    r'(RANHURA[ ]PENDULAR)|(RANHURA[ ]REDONDA)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_43(t):
    r'(ROSCAGEM[ ]NOVA)|(NOVA[ ]ROSCAGEM[ ]GS)|(FRESAR[ ]FURO)|(ROSCAR[ ]ROTURA[ ]APARA)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_44(t):
    r'(REBAIXAMENTO[ ]INVERTIDO)|(FURAR[ ]EM[ ]PROFUNDIDADE[ ]UNIVERSAL)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_45(t):
    r'(ALARGAR[ ]FURO)|(MANDRILAR)|(FURAR[ ]UNIVERSAL)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_46(t):
    r'(TOLERÂNCIA)|(SUPERFÍCIE[ ]CILÍNDRICA.[ ]CONTORNO)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_47(t):
    r'(ELABORAR[ ]DADOS[ ]DIGIT)|(PGM[ ]DIGIT.:[ ]BSP.H)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_48(t):
    r'(SUPERF.[ ]CILÍNDRICA)|(SUPERFÍCIE[ ]CILÍNDRICA)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_49(t):
    r'(TRAÇADO[ ]DO[ ]CONTORNO)|(FACTOR[ ]DE[ ]ESCALA[ ]ESPECÍF.[ ]EIXO)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_50(t):
    r'(PROFUNDIDADE[ ]ACABAMENTO)|(ACABAMENTO[ ]LATERAL)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_51(t):
    r'(PLANO[ ]DE[ ]MAQUINAÇÃO)|(DADOS[ ]DO[ ]CONTORNO)|(PRÉ-FURAR)|(DESBASTE)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_52(t):
    r'(ROSCAR[ ]GS)|(ROSCAGEM[ ]À[ ]LÂMINA)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_53(t):
    r'(ORIENTAÇÃO)|(ÂNGULO)|(CONTORNO)|(LABEL[ ]CONTORNO)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_54(t):
    r'(TEMPO[ ]DE[ ]ESPERA)|(ROTAÇÃO)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_55(t):
    r'(CAIXA[ ]CIRCULAR)|(RAIO)|(PONTO[ ]ZERO)|(ESPELHO)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_56(t):
    r'(TEMPO[ ]ESPERA)|(ROSCAR)|(FRESAR[ ]RANHURA)|(FRESAR[ ]CAIXA)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_57(t):
    r'(FURAR[ ]EM[ ]PROFUNDIDADE)|(PROFUNDIDADE)|(PASSO)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_58(t):
    r'(DATI[ ]PROFILO[ ]SAGOMATO)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_59(t):
    r'(FRESATURA[ ]DI[ ]FILETTATURE[ ]SU[ ]PREFORO)|(FRES.[ ]FILETT.ELICOID.)|(FRES[ ]FILETT.[ ]ESTERNE)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_60(t):
    r'(FRESATURA[ ]DI[ ]FILETTATURE[ ]CON[ ]SMUSSO)|(FRESATURA[ ]DI[ ]FILETTATURE)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_61(t):
    r'(ISOLA[ ]RETTANGOLARE)|(ISOLA[ ]CIRCOLARE)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_62(t):
    r'(TASCA[ ]RETTANGOLARE)|(TASCA[ ]CIRCOLARE)|(FRESATURA[ ]DI[ ]SCANALATURE)|(SCANALATURA[ ]CIRC.)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_63(t):
    r'(FRESATURA[ ]A[ ]SPIANARE)|(CENTRATURA)|(IMPOSTAZIONE[ ]ORIGINE)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_64(t):
    r'(SAGOMA[ ]CERCHIO)|(SAGOMA[ ]LINEE)|(SPIANATURA)|(SUPERFICIE[ ]REGOLARE)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_65(t):
    r'(FINITURA[ ]TASCHE[ ]CIRC.)|(FINITURA[ ]ISOLE[ ]CIRC.)|(FINITURA[ ]TASCHE)|(FINITURA[ ]ISOLE)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_66(t):
    r'(SCAN.[ ]CON[ ]PENDOL.)|(SCANALATURA[ ]CIRC.)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_67(t):
    r'(FRESATURA[ ]DI[ ]FORI)|(ROTT.[ ]TRUCIOLO[ ]IN[ ]MASCHIATURA)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_68(t):
    r'(MASCHIATURA[ ]NUOVO)|(MASCHIATURA[ ]RIGIDA[ ]NUOVO)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_69(t):
    r'(CONTROFORATURA[ ]INVERT.)|(FORATURA[ ]PROFONDA[ ]UNIVERSALE)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_70(t):
    r'(PROF.[ ]SU[ ]SUPERFICIE[ ]PROFILO)|(ALESATURA)|(TORNITURA)|(FORATURA[ ]UNIVERSALE)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_71(t):
    r'(SUPERFICIE[ ]CILINDRICA)|(ISOLA[ ]SU[ ]SUPERFICIE[ ]CILINDRICA)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_72(t):
    r'(FINITURA[ ]FONDO)|(FINITURA[ ]LATERALE)|(PROFILO[ ]SAGOMATO)|(FATT.[ ]SCALA[ ]SPECIF.)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_73(t):
    r'(DATI[ ]PROFILO)|(PREFORATURA)|(SVUOTAMENTO)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_74(t):
    r'(MASCHIATURA[ ]RIGIDA)|(FILETTATURA)|(PIANO[ ]DI[ ]LAVORO)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_75(t):
    r'(PROFILO)|(LABEL[ ]PROFILO)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_76(t):
    r'(ROTAZIONE)|(FATT.[ ]SCALA)|(ORIENTAMENTO)|(ANGOLO)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_77(t):
    r'(TASCA[ ]CIRCOLARE)|(RAGGIO)|(ORIGINE)|(LAV.[ ]SPECULARE)|(TEMPO[ ]DI[ ]SOSTA)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_78(t):
    r'(T.[ ]SOSTA)|(MASCHIATURA)|(FRESATURA[ ]DI[ ]SCANALATURE)|(FRESATURA[ ]DI[ ]TASCHE)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_79(t):
    r'(FORATURA[ ]PROFONDA)|(PROFOND)|(ACCOST)|(PASSO)|(FORATURA)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_80(t):
    r'(DATOS[ ]DEL[ ]TRAZADO[ ]DE[ ]CONTORNO)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_81(t):
    r'(FRESADO[ ]DE[ ]ROSCA[ ]EN[ ]TALADRO[ ]DE[ ]HÉLICE)|(FRESADO[ ]DE[ ]ROSCA[ ]EXTERIOR)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_82(t):
    r'(FRESADO[ ]ROSCA[ ]AVELLANADA)|(FRESADO[ ]DE[ ]ROSCA[ ]EN[ ]TALADRO)|(FRESADO[ ]DE[ ]ROSCA)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_83(t):
    r'(ISLA[ ]RECTANGULAR)|(ISLA[ ]CIRCULAR)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_84(t):
    r'(CAJERA[ ]RECTANGULAR)|(CAJERA[ ]CIRCULAR)|(FRESADO[ ]DE[ ]RANURAS)|(RANURA[ ]CIRCULAR)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_85(t):
    r'(FRESADO[ ]TRANSVERSAL)|(CENTRAJE)|(FIJAR[ ]PUNTO[ ]DE[ ]REFERENCIA)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_86(t):
    r'(CÍRCULO[ ]DE[ ]LA[ ]FIGURA)|(LÍNEAS[ ]DE[ ]LA[ ]FIGURA)|(PLANEADO)|(SUPERFICIE[ ]REGULAR)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_87(t):
    r'(ACABADO[ ]DE[ ]LA[ ]ISLA)|(ACABADO[ ]DE[ ]LA[ ]CAJERA[ ]CIRCULAR)|(ACABADO[ ]DE[ ]LA[ ]CAJERA)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_88(t):
    r'(RANURA[ ]PENDULAR)|(RANURA[ ]CIRCULAR)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_89(t):
    r'(ROSCADO[ ]NUEVO)|(ROSCADO[ ]RIGIDO[ ]GS[ ]NUEVP)|(FRESADO[ ]DE[ ]TALADRO)|(ROSCADO[ ]RIGIDO)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_90(t):
    r'(TALADRO[ ]UNIVERSAL)|(REBAJE[ ]INVERSO)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_91(t):
    r'(SUPERFICIE[ ]CILÍNDRICA[ ]CONTORNO)|(TALADRO)|(ESCARIADO)|(MANDRINADO)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_92(t):
    r'(SUPERFICIE[ ]CILÍNDRICA)|(SUPERFICIE[ ]CILÍNDRICA)|(SUPERFICIE[ ]CILÃNDRICA[ ]DE[ ]LA[ ]ISLA)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_93(t):
    r'(FACTOR[ ]DE[ ]ESCALA[ ]ESPEC.[ ]DE[ ]CADA[ ]EJE)|(FACTOR[ ]DE[ ]ESCALA)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_94(t):
    r'(ACABADO[ ]EN[ ]PROFUNDIDAD)|(ACABADO[ ]LATERAL)|(TRAZADO[ ]DEL[ ]CONTORNO)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_95(t):
    r'(PLANO[ ]INCLINADO)|(DATOS[ ]DEL[ ]CONTORNO)|(PRETALADRADO)|(DESBASTE)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_96(t):
    r'(ROSCADO[ ]RIGIDO)|(PASO[ ]ROSCA)|(ROSCADO[ ]A[ ]CUCHILLA)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_97(t):
    r'(ORIENTACIÓN)|(ÁNGULO)|(CONTORNO)|(LABEL[ ]DEL[ ]CONTORNO)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_98(t):
    r'(TIEMPO[ ]DE[ ]ESPERA)|(TPO.[ ]ESPERA)|(GIRO)|(FACTOR[ ]DE[ ]ESCALA)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_99(t):
    r'(CAJERA[ ]CIRCULAR)|(RADIO)|(PUNTO[ ]CERO)|(ESPEJO)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_100(t):
    r'(TPO.[ ]ESPERA)|(ROSCADO)|(FRESADO[ ]DE[ ]RANURAS)|(FRESADO[ ]DE[ ]CAJERAS)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_101(t):
    r'(TALADRADO[ ]PROFUNDO)|(DIST\.)|(PROFUNDIDAD)|(APROX)|(PASO)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_102(t):
    r'(FILET.[ ]HEL.[ ]AV.[ ]PERC.)|(FILET.[ ]EXT.[ ]SUR[ ]TENON)|(DONNÉES[ ]TRAC.[ ]CONTOUR)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_103(t):
    r'(FRAISAGE[ ]DE[ ]FILETS)|(FILETAGE[ ]SUR[ ]UN[ ]TOUR)|(FILETAGE[ ]AV.[ ]PERCAGE)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_104(t):
    r'(RAINURAGE)|(RAINURE[ ]PENDUL.)|(TENON[ ]RECTANGULAIRE)|(TENON[ ]CIRCULAIRE)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_105(t):
    r'(INIT.[ ]PT[ ]DE[ ]RÉF.)|(POCHE[ ]RECTANGULAIRE)|(POCHE[ ]CIRCULAIRE)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_106(t):
    r'(SURFACE[ ]RÉGULIÈRE)|(SURFAÇAGE)|(CENTRAGE)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_107(t):
    r'(CERCLE[ ]DE[ ]TROUS)|(GRILLE[ ]DE[ ]TROUS)|(LIGNE[ ]À[ ]LIGNE)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_108(t):
    r'(FINITION[ ]POCHE)|(FINITION[ ]TENON)|(FIN.[ ]POCHE[ ]CIRC.)|(FIN.[ ]TENON[ ]CIRC.)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_109(t):
    r'(TARAUD.[ ]BRISE-COP.)|(RAINURE[ ]PENDUL.)|(RAINURE[ ]CIRC.)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_110(t):
    r'(PERC.[ ]PROF.[ ]UNIVERS.)|(NOUVEAU[ ]TARAUDAGE)|(NOUV.[ ]TARAUDAGE[ ]RIG.)|(FRAISAGE[ ]DE[ ]TROUS)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_111(t):
    r'(ALES.[ ]A[ ]L\'ALESOIR)|(ALES.[ ]A[ ]L\'OUTIL)|(PERCAGE[ ]UNIVERS.)|(CONTRE-PERCAGE)|(PERCAGE)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_112(t):
    r'(CORPS[ ]DU[ ]CYLINDRE)|(CORPS[ ]CYLINDRE[ ]OBLONG[ ]CONV.)|(EXÉCUTION[ ]DONNÉES[ ]3D)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_113(t):
    r'(FINITION[ ]EN[ ]PROF.)|(FINITION[ ]LATÉRALE)|(TRACÉ[ ]DE[ ]CONTOUR)|(FACT.[ ]ÉCH.[ ]SPÉCIF.[ ]AXE)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_114(t):
    r'(FILETAGE)|(PLAN[ ]D\'USINAGE)|(DONNÉES[ ]CONTOUR)|(PRÉ-PERÇAGE)|(ÉVIDEMENT)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_115(t):
    r'(FACTEUR[ ]ÉCHELLE)|(LABEL[ ]CONTOUR)|(TARAUDAGE[ ]RIGIDE)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_116(t):
    r'(RAYON)|(POINT[ ]ZÉRO)|(IMAGE[ ]MIROIR)|(TEMPORISATION)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_117(t):
    r'(TARAUDAGE)|(RAINURAGE)|(FRAISAGE[ ]POCHES)|(POCHE[ ]CIRCULAIRE)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_118(t):
    r'(PERCAGE[ ]PROFOND)|(PROF.)|(PASSE)|(TEMPO.)|(PASS)|(PAS)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_119(t):
    r'(BEZUGSEBENE)|(BEZUGSPUNKT[ ]POLAR)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_120(t):
    r'(HELIX-BOHRGEWINDEFR.)|(HEL.[ ]THREAD[ ]DRLG/MLG)|(AUSSENGEWINDE[ ]FR.)|(OUTSIDE[ ]THREAD[ ]MLLNG)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_121(t):
    r'(BOHRGEWINDEFRAESEN)|(THREAD[ ]DRILLNG/MLLNG)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_122(t):
    r'(SENKGEWINDEFRAESEN)|(THREAD[ ]MILLING/COUNTERSINKING)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_123(t):
    r'(GEWINDEFRAESEN)|(THREAD[ ]MILLING)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_124(t):
    r'(ABZEILEN)|(MULTIPASS[ ]MILLNG)|(REGELFLAECHE)|(RULED[ ]SURFACE)|(BEZUGSPUNKT[ ]SETZEN)|(DATUM[ ]SETTING)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_125(t):
    r'(MUSTER[ ]KREIS)|(POLAR[ ]PATTERN)|(MUSTER[ ]LINIEN)|(CARTESIAN[ ]PATTRN)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_126(t):
    r'(KREIST.[ ]SCHLICHTEN)|(CIRCULAR[ ]POCKET[ ]FINISHING)|(KREISZ.[ ]SCHLICHTEN)|(C.[ ]STUD[ ]FINISHING)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_127(t):
    r'(TASCHE[ ]SCHLICHTEN)|(POCKET[ ]FINISHING)|(ZAPFEN[ ]SCHLICHTEN)|(STUD[ ]FINISHING)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_128(t):
    r'(NUT[ ]PENDELND)|(SLOT[ ]RECIP.[ ]PLNG)|(RUNDE[ ]NUT)|(CIRCULAR[ ]SLOT)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_129(t):
    r'(BOHRFRAESEN)|(BORE[ ]MILLING)|(GEW.-BOHREN[ ]SPANBR.)|(TAPPING[ ]W/[ ]CHIP[ ]BRKG)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_130(t):
    r'(GEWINDEBOHREN[ ]NEU)|(TAPPING[ ]NEW)|(GEW.-BOHREN[ ]GS[ ]NEU)|(RIGID[ ]TAPPING[ ]NEW)'
    t.type = "CYCLE_KEYWORD"
    return t
	
def t_CYCLE_KEYWORD_180(t):
    r'TAPPING'
    t.type = "CYCLE_KEYWORD"
    return t
	
def t_CYCLE_KEYWORD_131(t):
    r'(UNIVERSAL-TIEFBOHREN)|(UNIVERSAL[ ]PECKING)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_132(t):
    r'(RUECKWAERTS-SENKEN)|(BACK[ ]BORING)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_133(t):
    r'(UNIVERSAL-BOHREN)|(UNIVERSAL[ ]DRILLING)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_134(t):
    r'(BOHREN)|(DRILLING)|(REIBEN)|(REAMING)|(AUSDREHEN)|(BORING)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_135(t):
    r'(TOLERANZ)|(TOLERANCE)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_136(t):
    r'(PGM[ ]DIGIT.:)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_137(t):
    r'(DIGIDATEN[ ]ABARBEITEN)|(RUN[ ]DIGITIZED[ ]DATA)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_138(t):
    r'(ZYLINDER-MANTEL)|(CYLINDER[ ]SURFACE)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_139(t):
    r'(MASSFAKTOR[ ]ACHSSP.)|(AXIS-SPEC.[ ]SCALING)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_140(t):
    r'(KONTUR-ZUG)|(CONTOUR[ ]TRAIN)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_141(t):
    r'(SCHLICHTEN[ ]SEITE)|(SIDE[ ]FINISHING)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_142(t):
    r'(SCHLICHTEN[ ]TIEFE)|(FLOOR[ ]FINISHING)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_143(t):
    r'(RAEUMEN)|(ROUGH-OUT)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_144(t):
    r'(VORBOHREN)|(PILOT[ ]DRILLING)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_145(t):
    r'(KONTUR-DATEN)|(CONTOUR[ ]DATA)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_146(t):
    r'(BEARBEITUNGSEBENE)|(WORKING[ ]PLANE)|(WORK[ ]PLANE)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_147(t):
    r'(GEWINDESCHNEIDEN)|(THREAD[ ]CUTTING)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_148(t):
    r'(GEW.-BOHREN[ ]GS)|(GEW.[ ]-BOHREN[ ]GS)|(GEW.-[ ]BOHREN[ ]GS)|(GEW.[ ]-[ ]BOHREN[ ]GS)|(RIGID[ ]TAPPING)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_149(t):
    r'(CONTOUR[ ]GEOMETRY)|(KONTURLABEL)|(CONTOUR[ ]LABEL)|(KONTUR)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_150(t):
    r'(ORIENTIERUNG)|(ORIENTATION)|(WINKEL)|(ANGLE)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_151(t):
    r'(MASSFAKTOR)|(SCALING)|(SCL)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_152(t):
    r'(DREHUNG)|(ROTATION)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_153(t):
    r'(VERWEILZEIT)|(DWELL[ ]TIME)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_154(t):
    r'(SPIEGELN)|(MIRROR[ ]IMAGE)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_155(t):
    r'(NULLPUNKT)|(DATUM[ ]SHIFT)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_156(t):
    r'(KREISTASCHE)|(RADIUS)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_157(t):
    r'(TASCHENFRAESEN)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_158(t):
    r'(NUTENFRAESEN)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_159(t):
    r'(GEWINDEBOHREN)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_160(t):
    r'(TIEFBOHREN)|(PECKING)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_161(t):
    r'(SET[ ]UP)|(TIEFE)|(DEPTH)|(STEIG)|(PITCH)|(V.ZEIT)|(DWELL)|(ZUSTLG)|(PECKG)|(PLNGNG)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_8(t):
    r'(VRTANI)|(VYSTRUZENI)|(VYVRTAVANI)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_14(t):
    r'(SCHROEFDRAAD[ ]FREZEN[ ]MET[ ]VERZINKEN)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_16(t):
    r'(REFERENTIEPUNT[ ]VASTLEGGEN)|(KAMER)|(RONDKAMER)|(SLEUFFREZEN)'
    t.type = "CYCLE_KEYWORD"
    return t
#these 3 CYCLE_KEYWORD rules are handly

def t_CYCLE_KEYWORD_162(t):
    r'TOLERANCIA'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_163(t):
    r'TOLÉRANCE'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_164(t):
    r'PGM[ \t]CALL'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_165(t):
    r'PGM'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_166(t):
    r'TOLLERANZA'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_167(t):
    r'TRABAJAR[ ]CON[ ]DATOS[ ]3D'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_168(t):
    r'LAVORAZIONE[ ]DATI[ ]3D'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_169(t):
    r'PGM DIGIT.:[ ]BSP.H'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_170(t):
    r'CONTOUR'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_171(t):
    r'(SCHROEFDRAAD[ ]FREZEN)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_172(t):
    r'(FURAR)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_173(t):
    r'(HSC-SETUP[ ][(]TM[)])'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_174(t):
    r'(UNIVERSEEL-DIEPBOREN)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_175(t):
    r'(ARO[ ][(]TM[)])'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_176(t):
    r'(SCHRDR.BOR.[ ]SPAANBR.)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_177(t):
    r'(WT-BREUKCONTROLE)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_178(t):
    r'HSC-MODE:(0|1)[ ]TA(\d+\.\d*|\.\d+|[-+]?\d+)'
    t.type = "CYCLE_KEYWORD"
    return t

def t_CYCLE_KEYWORD_179(t):
    r'EINLIPPEN-BOHREN'
    t.type = "CYCLE_KEYWORD"
    return t
	
	
def t_CYCLE_KEYWORD_379(t):
    r'CICLO[ ]CABEZAL'
    t.type = "CYCLE_KEYWORD"
    return t

def t_TNC_LABEL_1(t):
    r'LBL[ \t]*\"[^\"\n]+\"'
    t.value = re.sub('[ \t]','',t.value)
    t.type = "TNC_LABEL"
    return t

def t_FNN(t):
    r'FN[ \t]*\d+:'
    m = re.search('\d+', t.value)
    if m is not None:
        index = int(m.group())
        if index >= 0 and index <= 28:
                t.type = "FN" + str(index)
                return t

def t_INC_AXIS(t):
    r'IX|IY|IZ|IA|IB|IC|IV|IW'
    return t

def t_ROT_DIR(t):
    r'DR2:|DR2|DR|DL'
    t.value = (t.value.partition(':'))[0]
    return t

def t_NORMAL(t):
    r'NX|NY|NZ'
    return t

def t_TOOLDIR(t):
    r'TX|TY|TZ'
    return t

def t_F_PARAM_1(t):
    r'F[ \t]+TCP'
    t.value = 'TCP'
    t.type = "F_PARAM"
    return t

def t_F_PARAM_2(t):
    r'F[ \t]+CONT'
    t.value = 'CONT'
    t.type = "F_PARAM"
    return t

def t_AXIS_PARAM_1(t):
    r'AXIS[ \t]+POS'
    t.value = 'POS'
    t.type = "AXIS_PARAM"
    return t

def t_AXIS_PARAM_2(t):
    r'AXIS[ \t]+SPAT'
    t.value = 'SPAT'
    t.type = 'AXIS_PARAM'
    return t

def t_PATHCTRL_PARAM_1(t):
    r'PATHCTRL[ \t]+AXIS'
    t.value = 'AXIS'
    t.type = 'PATHCTRL_PARAM'
    return t

def t_PATHCTRL_PARAM_2(t):
    r'PATHCTRL[ \t]+VECTOR'
    t.value = 'VECTOR'
    t.type = 'PATHCTRL_PARAM'
    return t

def t_DECIMALS(t):
    r'DECIMALS'
    return t

def t_PLANE_OP (t):
    r'PLANE'
    return t

def t_ABST_OP (t):
    r'(ABST)|(DIST)'
    return t
    
def t_CALL (t):
    r'CALL'
    return t

def t_SRC(t):
    r'SRC_'
    return t

def t_SEA(t):
    r'SEA_'
    return t

def t_BEG(t):
    r'BEG'
    return t

def t_UN_OP_1(t):
    r'SIN'
    t.value = NCExpressionFactory.SIN_OP
    t.type = "UN_OP"
    return t

def t_UN_OP_2(t):
    r'COS'
    t.value = NCExpressionFactory.COS_OP
    t.type = "UN_OP"
    return t

def t_UN_OP_3(t):
    r'TAN'
    t.value = NCExpressionFactory.TAN_OP
    t.type = "UN_OP"
    return t

def t_UN_OP_4(t):
    r'ACOS'
    t.value = NCExpressionFactory.ACOS_OP
    t.type = "UN_OP"
    return t

def t_UN_OP_5(t):
    r'ASIN'
    t.value = NCExpressionFactory.ASIN_OP
    t.type = "UN_OP"
    return t

def t_UN_OP_6(t):
    r'ATAN'
    t.value = NCExpressionFactory.ATAN_OP
    t.type = "UN_OP"
    return t

def t_UN_OP_7(t):
    r'ABS'
    t.value = NCExpressionFactory.ABS_OP
    t.type = "UN_OP"
    return t

def t_UN_OP_8(t):
    r'INT'
    t.value = NCExpressionFactory.ROUND_DOWN_OP
    t.type = "UN_OP"
    return t

def t_UN_OP_9(t):
    r'LN'
    t.value = NCExpressionFactory.LN_OP
    t.type = "UN_OP"
    return t

def t_UN_OP_10(t):
    r'LOG'
    t.value = NCExpressionFactory.LOG_OP
    t.type = "UN_OP"
    return t

def t_UN_OP_11(t):
    r'SQRT'
    t.value = NCExpressionFactory.SQRT_OP
    t.type = "UN_OP"
    return t

def t_UN_OP_12(t):
    r'NEG'
    t.value = NCExpressionFactory.NEG_OP
    t.type = "UN_OP"
    return t

def t_PLANE_AXIAL(t):
    r'AXIAL'
    return t

def t_FLOAT_VALUE_1(t):
    r'(\d*\.\d+)|(\d+\.\d*)'
    t.value = float(t.value)
    t.type = 'FLOAT_VALUE'
    return t

def t_FLOAT_VALUE_2(t):
    r'(\d*,\d+)|(\d+,\d*)'
    t.value = float(t.value.replace(',', '.'))
    t.type = 'FLOAT_VALUE'
    return t

def t_TNC_LABEL (t):
    r'LBL[ \t]*\d+'
    t.value = re.sub('[ \t]','',t.value)
    t.type = "TNC_LABEL"
    return t

def t_TNC_LABEL_PREFIX (t):
    r'LBL'
    return t

def t_ANGLE (t):
    r'ANG'
    return t

def t_LENGTH (t):
    r'LEN'
    return t

def t_CENTER_ANGLE (t):
    r'CCA'
    return t

def t_INC_POLAR_ANGLE (t):
    r'IPA'
    return t

def t_REP (t):
    r'REP'
    return t

def t_ROT_WORD (t):
    r'ROT'
    return t

def t_FUNC_11(t):
    r'CC'
    t.value = TNCFuncInfo(TNCFuncType.FUNC_CC, t.value)
    t.type = "FUNC"
    return t

def t_FUNC_12(t):
    r'FUNCTION[ \t]+TCPM'
    t.value = TNCFuncInfo(TNCFuncType.FUNC_TCPM, "TCPM")
    t.type = "FUNC"
    return t

def t_FUNC_13(t):
    r'FUNCTION[ \t]+RESET[ \t]+TCPM'
    t.value = TNCFuncInfo(TNCFuncType.FUNC_TCPM_RESET, "TCPM_RESET")
    t.type = "FUNC"
    return t

def t_FUNC_14(t):
    r'RND'
    t.value = TNCFuncInfo(TNCFuncType.FUNC_RND, t.value)
    t.type = "FUNC"
    return t

def t_FUNC_APPR_DEP(t):
    r'(APPR)|(DEP)'
    return t

def t_FUNC_ARG(t):
    r'CHF'
    t.value = TNCFuncInfo(TNCFuncType.FUNC_CHF, "CHF")
    return t

def t_POLAR_RADIUS (t):
    r'PR'
    return t

def t_POLAR_ANGLE (t):
    r'PA'
    return t

def t_LOOKAHEAD (t):
    r'LA'
    return t

def t_ID (t):
    r'ID'
    return t

def t_TNC_PI (t):
    r'PI'
    return t

def t_TNC_NE (t):
    r'NE'
    return t

def t_INTEGER_VALUE(t):
    r'[0-9]+'
    t.value = int(t.value)
    return t

def t_FUNC_1(t):
    r'L'
    t.value = TNCFuncInfo(TNCFuncType.FUNC_L, t.value)
    t.type = "FUNC"
    return t

def t_FUNC_15(t):
    r'C'
    if Core.g_nCurFunc == TNCFuncType.FUNC_NONE:
        t.value = TNCFuncInfo(TNCFuncType.FUNC_C, t.value)
        t.type = "FUNC"
    else:
        t.type = 'AXIS'

    return t

def t_R_WORD (t):
    r'R'
    return t

def t_TNC_SPINDLE (t):
    r'S'
    return t

def t_T_WORD (t):
    r'T'
    return t

def t_FEED (t):
    r'F'
    return t

def t_AXIS(t):
    r'X|Y|Z|A|B|U|V|W|E'
    return t

def t_STRING(t):
    r'\"[^\"\n]*\"'
    t.value = t.value[1:len(t.value)-1]
    return t

def t_EOL(t):
    r'(\n+)|(\r+)'
    t.lexer.lineno += t.value.count("\n")
    return t

def t_error(t):
    raise CseParseError

def start_path(lexer):
    lexer.code_start = lexer.lexpos        # Record the starting position
    lexer.begin("path")

def get_path(lexer):
    value = lexer.lexdata[lexer.code_start:lexer.code_end]
    return value

@lex.TOKEN(r"[a-zA-Z0-9_-]([a-zA-Z0-9_-]|[:\/\\\.,])*")
def t_path_path(t):
    t.lexer.code_end = t.lexer.lexpos
    pass

@lex.TOKEN(r".")
def t_path_quit(t):
    lexer.begin("INITIAL")
    pass
    
def start_programName(lexer):
    lexer.code_start = lexer.lexpos        # Record the starting position
    lexer.begin("programName")

def get_programName(lexer):
    value = lexer.lexdata[lexer.code_start:lexer.code_end]
    return value

@lex.TOKEN(r"LBL[ \t]*\"[^\"\n]+\" ")
def t_programName_label_1(t):
    t.lexer.code_end = t.lexer.lexpos
    pass

@lex.TOKEN(r"LBL[ \t]*\d+")
def t_programName_label_2(t):
    t.lexer.code_end = t.lexer.lexpos
    pass

@lex.TOKEN(r"\"[^\"\n]+\" ")
def t_programName_string(t):
    lexer.code_start += 1
    t.lexer.code_end = t.lexer.lexpos-1
    pass

@lex.TOKEN(r"[a-zA-Z0-9_-]([a-zA-Z0-9_-]|[:\/\\\., ])*")
def t_programName_path(t):
    if Core.g_nCurFunc == TNCFuncType.FUNC_BEGIN_PROGRAM or Core.g_nCurFunc == TNCFuncType.FUNC_END_PROGRAM:
        if t.value[len(t.value)-3:len(t.value)] == " MM":
            t.lexer.code_end = t.lexer.lexpos-3
            lexer.begin("INITIAL")
            t.value = "MM_MEASURE"
            t.type = "UNIT"
            return t
        if t.value[len(t.value)-5:len(t.value)] == " INCH":
            t.lexer.code_end = t.lexer.lexpos-5
            lexer.begin("INITIAL")
            t.value = "INCH_MEASURE"
            t.type = "UNIT"
            return t
        raise CseParseError
    elif Core.g_nCurFunc == TNCFuncType.FUNC_CALL_PROGRAM:
        t.lexer.code_end = t.lexer.lexpos
    else:
        pass

@lex.TOKEN(r".")
def t_programName_quit(t):
    lexer.begin("INITIAL")
    pass

def start_selectionName(lexer):
    lexer.code_start = lexer.lexpos        # Record the starting position
    lexer.begin("selectionName")

def get_selectionName(lexer):
    value = lexer.lexdata[lexer.code_start:lexer.code_end]
    return value    

@lex.TOKEN(r"\"[^\"\n]+\" ")
def t_selectionName_string(t):
    lexer.code_start += 1
    t.lexer.code_end = t.lexer.lexpos-1
    pass
   
@lex.TOKEN(r"[a-zA-Z0-9_-]([a-zA-Z0-9_-]|[:\/\\\.,])*")
def t_selectionName_path(t):
    t.lexer.code_end = t.lexer.lexpos
    pass

@lex.TOKEN(r".")
def t_selectionName_quit(t):
    lexer.begin("INITIAL")
    pass

def determineNewCycleID(value):
    index = 0
    while value[index].isdigit() == False:
        index += 1
    return int(float(value[index:len(value)+1]))

def determineOldCycleIDs(value):
    index = 0
    while value[index].isdigit() == False:
        index += 1
    pnID =  int(float(value[index:len(value)+1]))

    while value[index] != '.':
        index += 1
    index += 1

    pnSubID = int(value[index:len(value)+1])
    return (pnID, pnSubID)

if Core.Debug == 1:
    lexer = lex.lex(optimize=0, debug=0, errorlog = logger)
else:
    lexer = lex.lex(optimize=0, debug=0, errorlog = lex.NullLogger())

if __name__ == '__main__':
    while 1:
        s = input('input a code > ')
        if s == '``':
            print ("END")
            break
        lex.input(s)
        while True:
            tok = lex.token()
            if not tok: break
            print (tok)
