#
# History
#
# Date          Name                Description of Change
# 01-Mar-2018   Volker Grabowski    Initial version

import sys
import math
import CSE
from CSEWrapper import ChannelState
from CSEBasic import BasicMethods

class ControllerMethods(BasicMethods):
    def TOCHAR(channel : ChannelState, dValue : float, nDecimal : int) -> str:
        formatStr = '.' + str(nDecimal) + 'f'
        return format(dValue, formatStr)

    def SUBSTR(channel : ChannelState, strVal : str, nBeginIndex : int, nLength : int) -> str:
        if nBeginIndex < 0 or nLength < 0 or (nBeginIndex+nLength) > len(strVal):
            raise CSE.MethodError

        return strVal[nBeginIndex:nBeginIndex+nLength]

    def STRLEN(channel : ChannelState, string : str) -> int:
        return len(string)

    def STRCOMP(channel : ChannelState, strVal1 : str, strVal2 : str) -> int:
        if strVal1 == strVal2:
            return 0
        elif strVal1 < strVal2:
            return 1
        else:
            return -1

    def INSTR(channel : ChannelState, strVal1 : str, strVal2 : str, nBeg : int) -> str:
        return strVal1.find(strVal2, nBeg) + 1

    def IsSkipLevelSupported(channel : ChannelState, nLevel : int) -> bool:
        return nLevel == -1
