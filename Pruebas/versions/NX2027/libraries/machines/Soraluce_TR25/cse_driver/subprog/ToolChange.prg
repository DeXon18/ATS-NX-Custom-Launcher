0 BEGIN PGM TOOLCHANGE MM
1 M5
2 FN 18: SYSREAD Q1000 = ID20 NR2
3 FN 18: SYSREAD Q1001 = ID20 NR1
4 ; If actual tool identicall wiht preselected one skip AC block
5 FN 9: IF +Q1000 EQU +Q1001 GOTO LBL "NO_TOOLCHANGE"

0 ; Set the tool change position values in metric X,Y,Z
0 Q1001=0.0
0 Q1002=0.0
0 Q1003=0
0 Q1004=0

L Z1303.072 F1300 M91
L Y1021.294 F1300 M91

L  B0.0 A0.0 FMAX  
        
##LANGUAGE AC
	// deactivate softlimits and activate hard limits for the tool change
	activateSoftLimitCheck(FALSE);
##LANGUAGE NATIVE

##LANGUAGE AC
  INT nToolID;
  nToolID = getVariable ("Q1000");
  STRING strToolName;
  IF (nToolID > 0);
    generateTool (getToolNameByNumber(nToolID), "S");
  ENDIF;

  IF (exist(getCurrentTool("S")));
    visibility (     getCurrentTool("S"), OFF, TRUE);
    release    (     getCurrentTool("S"));
  ENDIF;

  IF (exist(getNextTool("S")));
    grasp      (     getNextTool("S"), getJunction("SPINDLE", "S"));
    position   (     getNextTool("S"), 0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
    visibility (     getNextTool("S"), ON,  TRUE);
    activateNextTool ("S");
  ENDIF;
##LANGUAGE NATIVE

##LANGUAGE AC
   // activate softlimits and activate hard limits for the tool change
   activateSoftLimitCheck(TRUE);
##LANGUAGE NATIVE

10 FN 17: SYSWRITE ID20 NR1 = +Q1000
11 LBL "NO_TOOLCHANGE"
12 M67
13 END PGM TOOLCHANGE MM
