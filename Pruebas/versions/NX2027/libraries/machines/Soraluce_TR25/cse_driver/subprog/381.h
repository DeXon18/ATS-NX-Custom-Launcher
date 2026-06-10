0  BEGIN PGM 381 MM 
1  ; ********************
2  ; HEAD SELECTION CYCLE
3  ; ********************
;COTAS PIC-KUP CABEZAL DIRECTO:*
;X-12114,4495
;Y+136,448
;Z-2683,722

;COTAS PIC-KUP CABEZAL 45_GRADOS:*
;X-12111,546
;Y+131,595
;Z-3533,439

FN 9: IF +Q1583 EQU +0 GOTO LBL 99
L B+0 C-180 R0 FMAX ;CAMBIO HTA
TOOL CALL 0
L B0 C0 FMAX

; SI CABEZAL YA CARGADO PRIMERO QUITAR
FN 9: IF +Q1584 EQU +1 GOTO LBL 51
FN 9: IF +Q1584 EQU +2 GOTO LBL 50
LBL 50
L X-12114,4495 Z-2683,722 M91 FMAX
L Y+136,448 M91 FMAX
;FN 17: SYSWRITE Q1582 = CABEZAL_ZAYER_DIRECTO
FN 9: IF +0 EQU +0 GOTO LBL 52
LBL 51
L X-12111,546  Z-3533,439 M91 FMAX
L Y+131,595 M91 FMAX
LBL 52
##LANGUAGE AC
  STRING sHeadNameold;
  STRING sCarrierold;
  STRING sUnionold;
  INT sHeadNumberold;
  sHeadNumberold = getVariable("Q1584");
   IF (sHeadNumberold == 1 );
		sHeadNameold = "CABEZAL_AUTO_ZAYER";
	    sCarrierold  = "H1_POCKET";
		sUnionold = "H1";
   ELSE;
		sHeadNameold = "CABEZAL_DIRECTO_ZAYER";
	    sCarrierold  = "H2_POCKET";
		sUnionold = "H2";
   ENDIF;

  grasp    (  sHeadNameold, getJunction(sCarrierold,sUnionold));
  position (  sHeadNameold, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
  unmountHead("S");

##LANGUAGE NATIVE
L Y+1052,314 M91 FMAX

; CARGAR NUEVO CABEZAL
LBL 99
FN 9: IF +Q1581 EQU +1 GOTO LBL 200
FN 9: IF +Q1581 EQU +2 GOTO LBL 100
LBL 100
L X-12114,4495 Z-2683,722 M91 FMAX
L Y+136,448 M91 FMAX
;FN 17: SYSWRITE Q1582 = CABEZAL_ZAYER_DIRECTO
FN 9: IF +0 EQU +0 GOTO LBL 300
LBL 200
L X-12111,546  Z-3533,439 M91 FMAX
L Y+131,595 M91 FMAX
LBL 300
Q1582 = Q1581

##LANGUAGE AC
  STRING sHeadName;
  INT sHeadNumber;
  sHeadNumber = getVariable("Q1581");
   IF (sHeadNumber == 1 );
		sHeadName = "CABEZAL_AUTO_ZAYER";
   ELSE;
		sHeadName = "CABEZAL_DIRECTO_ZAYER";
   ENDIF;

  // make sure an existing S axis will be removed prior the S axis from
  // the head will registered with mountHead command
  detachJoint("S"); 
  mountHead(sHeadName, "S");
  grasp    ( sHeadName, getJunction("HEADCARRIER", "S"));
  position ( sHeadName, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
##LANGUAGE NATIVE

L Y+1052,314 M91 FMAX

LBL 999
Q1583 = 1 ;Ya tiene cabezal activo
Q1584 = Q1581 ; Cabezal anterior
M998
END PGM 381 MM 
