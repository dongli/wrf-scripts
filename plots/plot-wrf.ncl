f = addfile(file_path, "r")

wks = gsn_open_wks("pdf", "wrf-plot")

tmp = wrf_user_getvar(f, "tc", -1)
tmp_850 = wrf_user_vert_interp(f, tmp, "pressure", (/850/), True)

u = wrf_user_getvar(f, "ua", -1)
v = wrf_user_getvar(f, "va", -1)
u_850 = wrf_user_vert_interp(f, u, "pressure", (/850/), True)
v_850 = wrf_user_vert_interp(f, v, "pressure", (/850/), True)

res_tmp = True
res_tmp@cnFillOn = True
res_tmp@cnLevelSelectionMode = "ManualLevels"
res_tmp@cnMinLevelValF = 6.0
res_tmp@cnMaxLevelValF = 16.0
res_tmp@cnLevelSpacingF = 0.5

res_wnd = True
res_wnd@vcWindBarbScaleFactorF = 1.9438
res_wnd@vcWindBarbTickLengthF = 0.6
res_wnd@vcLineArrowThicknessF = 2.0
res_wnd@vcRefAnnoOrthogonalPosF = -0.125
res_wnd@vcRefMagnitudeF = 1.0
res_wnd@vcRefLengthF = 0.02
res_wnd@vcMinFracLengthF = 0.5
res_wnd@vcMinDistanceF = 0.02

res_map = True
res_map@mpDataSetName = "Earth..4"
res_map@mpDataBaseVersion = "MediumRes"
res_map@mpGeophysicalLineColor = "Black"
res_map@mpCountryLineColor = "Black"
res_map@mpOutlineSpecifiers = "China:states"
res_map@mpCountyLineThicknessF = 3.0

do i = 1, 6
  print(i)
  plot_tmp = wrf_contour(f, wks, tmp_850(i,0,:,:), res_tmp)
  plot_wnd = wrf_vector(f, wks, u_850(i,0,:,:), v_850(i,0,:,:), res_wnd)

  over = wrf_map_overlays(f, wks, (/plot_tmp,plot_wnd/), True, True)
end do
