########################## TCL Event Handlers ########################## 
# 
#  Soraluce_FLP8000.tcl 
# 
#  Creado por bugalde  @  20200627 16:48:02,58 
#  con PPcrypt version 1.0.1 
# 
######################################################################## 
  
set cam_aux_dir [MOM_ask_env_var NX_CLIENTE_CAM_POST_DIR] 
  
catch { 
	MOM_run_user_function ${cam_aux_dir}PPdecrypt.dll ufusr 
	PPdecrypt ${cam_aux_dir}Soraluce_FLP8000_enc.tcl 
} 
