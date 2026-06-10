#
# History
#
# Date          Name                Description of Change
# 10-Jul-2013   Kevin Chen          Creation
# 28-Jan-2014   Jason Fu            Add preprocessing function to method ParseNCLine
# 08-Oct-2015   Volker Grabowski    Remove redundant casts in command and method implementations
# 09-Aug-2016   Volker Grabowski    Use custom exception class to handle parse errors
# 02-Sep-2016   Volker Grabowski    Move CseParseError to CSEWrapper.py

import sys
import os

if "UGII_CAM_AUXILIARY_DIR" in os.environ:
    sys.path.append(os.environ['UGII_CAM_AUXILIARY_DIR'] + r'\cse')
elif "UGII_CAM_BASE_DIR" in os.environ:
    sys.path.append(os.environ['UGII_CAM_BASE_DIR']+r'\auxiliary\cse')
elif "UGII_BASE_DIR" in os.environ:
    sys.path.append(os.environ['UGII_BASE_DIR']+r'\mach\auxiliary\cse')

import CSEWrapper
from CSEWrapper import NCBasicType
from CSEWrapper import VariableManager
import CseTNC_Yacc

class Controller:
    def __init__(self):
        self.m_NCParser = CseTNC_Yacc.Parser()
        self.m_ExprParser =  CseTNC_Yacc.ParserExpr()
        self.m_ctrlMethod = ControllerMethod()

    def ParseNCLine(self, strLine, callFactory):
        self.m_NCParser.SetCallFactory(callFactory)
        strLine = strLine.lstrip()
        strLine = strLine.rstrip()

        if len(strLine) == 0:
            return True

        if strLine[len(strLine)-1] != '~':
            return self.m_NCParser.parse(strLine)

        strLine = strLine[: len(strLine)-1]

        #Remove comment of first line
        nIndex = strLine.find(';',0,len(strLine))
        if nIndex > 0:
            strCompleteLine = strLine[: nIndex]
        elif nIndex == 0:
            strCompleteLine = ""
        else:
            strCompleteLine = strLine

        while True:
            strLine = callFactory.GetNextLine()
            strLine = strLine.lstrip()
            strLine = strLine.rstrip()
            
            if len(strLine) != 0:
                if strLine[len(strLine)-1] != '~':
                    strCompleteLine = strCompleteLine + strLine
                    break
                else:
                    strLine = strLine[: len(strLine)-1]

            #Remove comment
            nIndex = strLine.find(';',0,len(strLine))            
            if nIndex > 0:
                strLine = strLine[: nIndex]
            elif nIndex == 0:
                strLine = ""

            strCompleteLine = strCompleteLine + strLine + " "

        return self.m_NCParser.parse(strCompleteLine)

    def ParseNCExpression(self, strLine, exprsys):
        self.m_ExprParser.SetExprSystem(exprsys)
        return self.m_ExprParser.parse(strLine)

    def ExecuteCommand(self, strCommandName, listArgsNC, state):
        return False

    def HasMethod(self, strMethodName):
        if strMethodName == "ResetControllerState":
            return True
        elif strMethodName == "TOCHAR":
            return True
        elif strMethodName == "SUBSTR":
            return True
        elif strMethodName == "STRLEN":
            return True
        elif strMethodName == "STRCOMP":
            return True
        elif strMethodName == "INSTR":
            return True

        return False

    def GetMethodType(self, strMethodName, exprSystem):
        if strMethodName == "ResetControllerState":
            return None
        elif strMethodName == "TOCHAR":
            return exprSystem.CreateBasicType(NCBasicType.STRING)
        elif strMethodName == "SUBSTR":
            return exprSystem.CreateBasicType(NCBasicType.STRING)
        elif strMethodName == "STRLEN":
            return exprSystem.CreateBasicType(NCBasicType.INTEGER)
        elif strMethodName == "STRCOMP":
            return exprSystem.CreateBasicType(NCBasicType.INTEGER)
        elif strMethodName == "INSTR":
            return exprSystem.CreateBasicType(NCBasicType.INTEGER)

        return None


    def ExecuteMethod(self, strMethodName, listArgs, exprSystem):
        if strMethodName == "ResetControllerState":
            return None
        elif strMethodName == "TOCHAR":
            return self.m_ctrlMethod.TOCHAR(listArgs, exprSystem)
        elif strMethodName == "SUBSTR":
            return self.m_ctrlMethod.SUBSTR(listArgs, exprSystem)
        elif strMethodName == "STRLEN":
            return self.m_ctrlMethod.STRLEN(listArgs, exprSystem)
        elif strMethodName == "STRCOMP":
            return self.m_ctrlMethod.STRCOMP(listArgs, exprSystem)
        elif strMethodName == "INSTR":
            return self.m_ctrlMethod.INSTR(listArgs, exprSystem)

        return None

    def InitializeChannel(self, state):
        newTNCCtrState = ControllerState()
        newTNCCtrState.InitializeChannel(state)
        return newTNCCtrState

    def CloneChannel(self, channelobj, state):
        return channelobj.Clone(state)

class ControllerMethod:
    def TOCHAR(self, listArgs, exprSystem):
        dValue = listArgs[0].GetDouble()
        nDecimal = listArgs[1].GetInteger()
        formatStr = '.' + str(nDecimal) + 'f'

        return exprSystem.GetValueFactory().CreateStringValue(format(dValue, formatStr))


    def SUBSTR(self, listArgs, exprSystem):
        strVal = listArgs[0].GetString()
        nBeginIndex = listArgs[1].GetInteger()
        nLength = listArgs[2].GetInteger()

        if nBeginIndex < 0 or nLength < 0 or (nBeginIndex+nLength) > len(strVal):
            return False

        return exprSystem.GetValueFactory().CreateStringValue(strVal[nBeginIndex:nBeginIndex+nLength])

    def STRLEN(self, listArgs, exprSystem):
        nLen = len(listArgs[0].GetString())
        return exprSystem.GetValueFactory().CreateIntegerValue(nLen)

    def STRCOMP(self, listArgs, exprSystem):
        strVal1 = listArgs[0].GetString()
        strVal2 = listArgs[1].GetString()
        retValue = -1
        if strVal1 == strVal2:
            retValue = 0
        elif strVal1 < strVal2:
            retValue = 1

        return exprSystem.GetValueFactory().CreateIntegerValue(retValue)

    def INSTR(self, listArgs, exprSystem):
        strVal1 = listArgs[0].GetString()
        strVal2 = listArgs[1].GetString()
        nBeg = listArgs[2].GetInteger()

        retVal = strVal1.find(strVal2, nBeg)

        retVal = retVal + 1

        return exprSystem.GetValueFactory().CreateIntegerValue(retVal)

class ControllerState:
    def __init__(self):
        self.m_strLastJointName = ''

    def Clone(self, state):
        newTNCCtrState = ControllerState()
        newTNCCtrState.m_strLastJointName = ''
        newTNCCtrState.m_strLastJointName = self.m_strLastJointName

        return newTNCCtrState

    def InitializeChannel(self, state):
        exprSystem = state.GetExprSystem()
        varManager = exprSystem.GetVarManager()
        varManager.SetVarAccessMode(VariableManager.GLOBAL_ONLY)
        varManager.ActivateAutoDeclare(True)
        varManager.AllowMultiDeclare(True)

        return None

def CreateController():
        return CSEWrapper.Controller(Controller())
