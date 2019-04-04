cost_fn = readAsciiTable("./cost_fn", 12, "float", 2)
grad_fn = readAsciiTable("./grad_fn", 11, "float", 2)

dims = dimsizes(cost_fn)

num_iter = dims(0)

wks = gsn_open_wks("pdf", "cost_grad_fn")

res = True
res@gsnDraw = False
res@gsnFrame = False
res@tiXAxisString = "Iterations"
res@xyLineColor = "red"
res@xyLineThicknessF = 3

res@tiYAxisString = "Cost"
plot0 = gsn_csm_xy(wks, ispan(0, num_iter - 1, 1), cost_fn(:,3), res)

res@tiYAxisString = "Gradient"
plot1 = gsn_csm_xy(wks, ispan(0, num_iter - 1, 1), grad_fn(:,3), res)

gsn_panel(wks, (/plot0,plot1/), (/1,2/), False)
