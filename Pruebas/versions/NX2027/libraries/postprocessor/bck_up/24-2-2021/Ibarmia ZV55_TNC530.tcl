########################## TCL Event Handlers ########################## 
# 
#  Ibarmia ZV55_TNC530.tcl 
# 
#  Creado por bugalde  @  24/02/2021 13:24:22,36 
#  con PPcrypt version 1.0.1 
# 
######################################################################## 
  
set cam_aux_dir [MOM_ask_env_var NX_CLIENTE_CAM_POST_DIR] 
  
catch { 
	MOM_run_user_function ${cam_aux_dir}PPdecrypt.dll ufusr 
	PPdecrypt ${cam_aux_dir}Ibarmia ZV55_TNC530_enc.tcl 
} 
