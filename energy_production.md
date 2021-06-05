The goal is to predict the quantity of energy from renewable sources
that can be produced in an hour and in a day in Italy.

In this notebook we will start exploring the joint dataset of weather
records and energy production data. We will then move to fitting and
evaluating different models to predict the amount of energy that can be
produced from different renewable sources.

    df_terna <- read.csv("data.csv")
    colnames(df_terna) <- c("Date","GWh","EnergySource")
    df_terna$EnergySource <- factor(df_terna$EnergySource)
    head(df_terna)

    ##                  Date  GWh EnergySource
    ## 1 2021-01-01 00:00:00 1.47      Biomass
    ## 2 2021-01-01 00:00:00 0.62   Geothermal
    ## 3 2021-01-01 00:00:00 3.65        Hydro
    ## 4 2021-01-01 00:00:00 0.00 Photovoltaic
    ## 5 2021-01-01 00:00:00 2.65         Wind
    ## 6 2021-01-01 01:00:00 1.44      Biomass

    biomass <- read.csv("Biomass.csv")
    geothermal <- read.csv("Geothermal.csv")
    hydro <- read.csv("Hydro.csv")
    photovoltaic <- read.csv("Photovoltaic.csv")
    wind <- read.csv("Wind.csv")
    head(biomass)

    ##                  Date humidity    temp rain_1h snow_1h wind_deg wind_speed
    ## 1 2021-04-27 13:00:00    68.80 15.6185   0.047       0   164.50     3.9865
    ## 2 2021-04-27 14:00:00    69.65 15.5185   0.021       0   142.75     4.3635
    ## 3 2021-04-27 15:00:00    70.70 15.6285   0.028       0   148.20     3.6885
    ## 4 2021-04-27 16:00:00    73.65 14.8430   0.080       0   171.15     3.4315
    ## 5 2021-04-27 17:00:00    75.60 14.1630   0.000       0   141.55     2.6865
    ## 6 2021-04-27 18:00:00    78.55 13.4855   0.016       0   130.30     2.9840
    ##   directnormalirradiance diffusehorizontalirradiance
    ## 1              155.71700                   238.36000
    ## 2              159.54900                   196.94900
    ## 3              150.91850                   161.54300
    ## 4              121.42000                   123.68450
    ## 5              117.22050                    70.78650
    ## 6               16.98225                    20.83338
    ##   globalhorizontalirradiance_2 directnormalirradiance_2
    ## 1                    864.18300                 910.5950
    ## 2                    759.42150                 882.6240
    ## 3                    609.63600                 833.9465
    ## 4                    428.86000                 753.7170
    ## 5                    236.21450                 614.1775
    ## 6                     61.89262                 311.8944
    ##   diffusehorizontalirradiance_2 RenewableGeneration_Biomass
    ## 1                     116.42250                        2.47
    ## 2                     110.68300                        2.56
    ## 3                     101.42350                        2.51
    ## 4                      87.83850                        2.55
    ## 5                      68.05600                        2.48
    ## 6                      35.67588                        2.41

    library(ggcorrplot)
    library(ggplot2)
    library(ggthemes)
    cov_matrix <- cor(biomass[,-1])
    ggcorrplot(cov_matrix, method="square", type="lower", title="Correlation plot\n",
    ggtheme=theme_tufte(), show.diag=T)

![](energy_production_files/figure-markdown_strict/unnamed-chunk-3-1.png)

    library("lubridate") 
    biomass$Hour <- factor(hour(biomass$Date))
    biomass$Month <- format(as.Date(biomass$Date), "%m")
    biomass <- subset(biomass, select = -1)

    geothermal$Hour <- factor(hour(geothermal$Date))
    geothermal$Month <- format(as.Date(geothermal$Date), "%m")
    geothermal <- subset(geothermal, select = -1)

    hydro$Hour <- factor(hour(hydro$Date))
    hydro$Month <- format(as.Date(hydro$Date), "%m")
    hydro <- subset(hydro, select = -1)

    photovoltaic$Hour <- factor(hour(photovoltaic$Date))
    photovoltaic$Month <- format(as.Date(photovoltaic$Date), "%m")
    photovoltaic <- subset(photovoltaic, select = -1)

    wind$Hour <- factor(hour(wind$Date))
    wind$Month <- format(as.Date(wind$Date), "%m")
    wind <- subset(wind, select = -1)

    # train-test division
    set.seed(30)
    train_indexes <- sample(nrow(biomass),0.7*nrow(biomass))
    train_bio <- biomass[train_indexes,]
    test_x_bio <- biomass[-train_indexes,-c(12)]
    test_y_bio <- biomass[-train_indexes,12]

    set.seed(30)
    train_indexes <- sample(nrow(geothermal),0.7*nrow(geothermal))
    train_geo <- geothermal[train_indexes,]
    test_x_geo <- geothermal[-train_indexes,-c(12)]
    test_y_geo <- geothermal[-train_indexes,12]
    #
    train_indexes <- sample(nrow(hydro),0.7*nrow(hydro))
    train_hydro <- hydro[train_indexes,]
    test_x_hydro <- hydro[-train_indexes,-c(12)]
    test_y_hydro <- hydro[-train_indexes,12]
    #
    train_indexes <- sample(nrow(photovoltaic),0.7*nrow(photovoltaic))
    train_photo <- photovoltaic[train_indexes,]
    test_x_photo <- photovoltaic[-train_indexes,-c(12)]
    test_y_photo <- photovoltaic[-train_indexes,12]
    #
    train_indexes <- sample(nrow(wind),0.7*nrow(wind))
    train_wind <- wind[train_indexes,]
    test_x_wind <- wind[-train_indexes,-c(12)]
    test_y_wind <- wind[-train_indexes,12]

    # linear regression with LS
    # Biomass
    LS_bio <- glm(RenewableGeneration_Biomass~.,data=train_bio)
    summary(LS_bio)

    ## 
    ## Call:
    ## glm(formula = RenewableGeneration_Biomass ~ ., data = train_bio)
    ## 
    ## Deviance Residuals: 
    ##      Min        1Q    Median        3Q       Max  
    ## -0.83458  -0.18766   0.02683   0.19195   0.63811  
    ## 
    ## Coefficients:
    ##                                 Estimate Std. Error t value Pr(>|t|)    
    ## (Intercept)                    2.7819733  0.5434409   5.119 6.90e-07 ***
    ## humidity                      -0.0002127  0.0045325  -0.047 0.962607    
    ## temp                          -0.0498663  0.0169077  -2.949 0.003544 ** 
    ## rain_1h                       -0.1583932  0.1130793  -1.401 0.162765    
    ## snow_1h                       -2.1455362  1.9273963  -1.113 0.266898    
    ## wind_deg                      -0.0004144  0.0008748  -0.474 0.636176    
    ## wind_speed                     0.0067212  0.0396048   0.170 0.865404    
    ## directnormalirradiance         0.0002326  0.0003187   0.730 0.466420    
    ## diffusehorizontalirradiance    0.0001147  0.0017890   0.064 0.948935    
    ## globalhorizontalirradiance_2   0.0351542  0.0078401   4.484 1.20e-05 ***
    ## directnormalirradiance_2       0.0357411  0.0173553   2.059 0.040685 *  
    ## diffusehorizontalirradiance_2 -0.4673040  0.1983094  -2.356 0.019367 *  
    ## Hour1                         -0.1471417  0.1311304  -1.122 0.263094    
    ## Hour2                         -0.2355883  0.1436004  -1.641 0.102374    
    ## Hour3                         -0.2958775  0.1390346  -2.128 0.034490 *  
    ## Hour4                         -0.1224457  0.1345854  -0.910 0.363967    
    ## Hour5                          3.4215486  1.4146183   2.419 0.016424 *  
    ## Hour6                          1.9956824  1.7004910   1.174 0.241882    
    ## Hour7                         -0.2614304  2.2218624  -0.118 0.906447    
    ## Hour8                         -2.9983514  2.7376027  -1.095 0.274657    
    ## Hour9                         -5.6271554  3.1627596  -1.779 0.076648 .  
    ## Hour10                        -7.9093483  3.5001616  -2.260 0.024861 *  
    ## Hour11                        -9.1067729  3.6889432  -2.469 0.014356 *  
    ## Hour12                        -9.4602669  3.7080033  -2.551 0.011440 *  
    ## Hour13                        -8.4515551  3.5594495  -2.374 0.018474 *  
    ## Hour14                        -6.3505253  3.2590702  -1.949 0.052673 .  
    ## Hour15                        -3.7317226  2.8487899  -1.310 0.191643    
    ## Hour16                        -0.7243802  2.3400076  -0.310 0.757199    
    ## Hour17                         1.8169679  1.8171525   1.000 0.318505    
    ## Hour18                         3.7028103  1.4272216   2.594 0.010139 *  
    ## Hour19                         0.9774834  0.2531338   3.862 0.000150 ***
    ## Hour20                         0.5641048  0.1384320   4.075 6.52e-05 ***
    ## Hour21                         0.4768442  0.1305378   3.653 0.000327 ***
    ## Hour22                         0.2932812  0.1315404   2.230 0.026828 *  
    ## Hour23                         0.0930646  0.1238483   0.751 0.453225    
    ## Month05                       -0.0758156  0.0762291  -0.995 0.321082    
    ## ---
    ## Signif. codes:  0 '***' 0.001 '**' 0.01 '*' 0.05 '.' 0.1 ' ' 1
    ## 
    ## (Dispersion parameter for gaussian family taken to be 0.09360543)
    ## 
    ##     Null deviance: 35.092  on 246  degrees of freedom
    ## Residual deviance: 19.751  on 211  degrees of freedom
    ## AIC: 150.98
    ## 
    ## Number of Fisher Scoring iterations: 2

    pred <- predict(LS_bio,test_x_bio)
    MSE_bio <- mean((pred-test_y_bio)^2)
    print(MSE_bio)

    ## [1] 0.1139999

    library(MASS)
    step_bio <- stepAIC(LS_bio, direction = "both",trace = F)
    step_bio$anova

    ## Stepwise Model Path 
    ## Analysis of Deviance Table
    ## 
    ## Initial Model:
    ## RenewableGeneration_Biomass ~ humidity + temp + rain_1h + snow_1h + 
    ##     wind_deg + wind_speed + directnormalirradiance + diffusehorizontalirradiance + 
    ##     globalhorizontalirradiance_2 + directnormalirradiance_2 + 
    ##     diffusehorizontalirradiance_2 + Hour + Month
    ## 
    ## Final Model:
    ## RenewableGeneration_Biomass ~ temp + rain_1h + globalhorizontalirradiance_2 + 
    ##     directnormalirradiance_2 + diffusehorizontalirradiance_2 + 
    ##     Hour + Month
    ## 
    ## 
    ##                            Step Df     Deviance Resid. Df Resid. Dev      AIC
    ## 1                                                     211   19.75075 150.9850
    ## 2                    - humidity  1 0.0002062293       212   19.75095 148.9875
    ## 3 - diffusehorizontalirradiance  1 0.0005229549       213   19.75148 146.9941
    ## 4                  - wind_speed  1 0.0030927930       214   19.75457 145.0328
    ## 5                    - wind_deg  1 0.0192063212       215   19.77377 143.2728
    ## 6      - directnormalirradiance  1 0.0672231238       216   19.84100 142.1111
    ## 7                     - snow_1h  1 0.1302367115       217   19.97123 141.7271

    LSr_bio <- glm(formula(step_bio), data=train_bio)
    pred <- predict(LSr_bio,test_x_bio)
    MSE_bior <- mean((pred-test_y_bio)^2)
    print(c(MSE_bio,MSE_bior))

    ## [1] 0.1139999 0.1121128

    # geothermal
    # LS
    LS_geo <- glm(RenewableGeneration_Geothermal~.,data=train_geo)
    summary(LS_geo)

    ## 
    ## Call:
    ## glm(formula = RenewableGeneration_Geothermal ~ ., data = train_geo)
    ## 
    ## Deviance Residuals: 
    ##       Min         1Q     Median         3Q        Max  
    ## -0.035247  -0.005551   0.001420   0.006631   0.025063  
    ## 
    ## Coefficients:
    ##                                 Estimate Std. Error t value Pr(>|t|)    
    ## (Intercept)                    7.323e-01  2.150e-02  34.061  < 2e-16 ***
    ## humidity                      -7.326e-04  1.793e-04  -4.086 6.25e-05 ***
    ## temp                          -2.320e-03  6.689e-04  -3.469 0.000633 ***
    ## rain_1h                       -7.970e-03  4.474e-03  -1.782 0.076260 .  
    ## snow_1h                       -1.222e-02  7.625e-02  -0.160 0.872813    
    ## wind_deg                      -1.723e-05  3.461e-05  -0.498 0.619174    
    ## wind_speed                     1.818e-04  1.567e-03   0.116 0.907715    
    ## directnormalirradiance        -1.172e-05  1.261e-05  -0.929 0.353742    
    ## diffusehorizontalirradiance    4.937e-05  7.077e-05   0.698 0.486247    
    ## globalhorizontalirradiance_2  -1.243e-03  3.102e-04  -4.008 8.48e-05 ***
    ## directnormalirradiance_2      -5.444e-04  6.866e-04  -0.793 0.428706    
    ## diffusehorizontalirradiance_2  7.194e-03  7.845e-03   0.917 0.360216    
    ## Hour1                         -1.704e-03  5.188e-03  -0.329 0.742834    
    ## Hour2                          5.983e-04  5.681e-03   0.105 0.916228    
    ## Hour3                         -6.636e-03  5.500e-03  -1.207 0.228971    
    ## Hour4                         -3.740e-03  5.324e-03  -0.702 0.483211    
    ## Hour5                         -2.996e-02  5.596e-02  -0.535 0.592988    
    ## Hour6                          1.070e-01  6.727e-02   1.590 0.113353    
    ## Hour7                          2.791e-01  8.790e-02   3.175 0.001724 ** 
    ## Hour8                          4.467e-01  1.083e-01   4.125 5.34e-05 ***
    ## Hour9                          5.905e-01  1.251e-01   4.720 4.30e-06 ***
    ## Hour10                         7.075e-01  1.385e-01   5.110 7.21e-07 ***
    ## Hour11                         7.669e-01  1.459e-01   5.255 3.62e-07 ***
    ## Hour12                         7.806e-01  1.467e-01   5.321 2.63e-07 ***
    ## Hour13                         7.285e-01  1.408e-01   5.173 5.34e-07 ***
    ## Hour14                         6.235e-01  1.289e-01   4.836 2.56e-06 ***
    ## Hour15                         4.871e-01  1.127e-01   4.322 2.38e-05 ***
    ## Hour16                         3.135e-01  9.257e-02   3.386 0.000845 ***
    ## Hour17                         1.442e-01  7.189e-02   2.006 0.046112 *  
    ## Hour18                        -3.460e-03  5.646e-02  -0.061 0.951188    
    ## Hour19                        -1.137e-02  1.001e-02  -1.135 0.257550    
    ## Hour20                        -1.968e-04  5.477e-03  -0.036 0.971361    
    ## Hour21                        -3.421e-03  5.164e-03  -0.662 0.508443    
    ## Hour22                         4.979e-04  5.204e-03   0.096 0.923861    
    ## Hour23                        -3.545e-03  4.900e-03  -0.724 0.470117    
    ## Month05                        6.050e-03  3.016e-03   2.006 0.046125 *  
    ## ---
    ## Signif. codes:  0 '***' 0.001 '**' 0.01 '*' 0.05 '.' 0.1 ' ' 1
    ## 
    ## (Dispersion parameter for gaussian family taken to be 0.0001464991)
    ## 
    ##     Null deviance: 0.066238  on 246  degrees of freedom
    ## Residual deviance: 0.030911  on 211  degrees of freedom
    ## AIC: -1444.6
    ## 
    ## Number of Fisher Scoring iterations: 2

    pred <- predict(LS_bio,test_x_geo)
    MSE_geo <- mean((pred-test_y_geo)^2)
    # reduced
    step_geo <- stepAIC(LS_geo, direction = "both",trace = F)
    step_geo$anova

    ## Stepwise Model Path 
    ## Analysis of Deviance Table
    ## 
    ## Initial Model:
    ## RenewableGeneration_Geothermal ~ humidity + temp + rain_1h + 
    ##     snow_1h + wind_deg + wind_speed + directnormalirradiance + 
    ##     diffusehorizontalirradiance + globalhorizontalirradiance_2 + 
    ##     directnormalirradiance_2 + diffusehorizontalirradiance_2 + 
    ##     Hour + Month
    ## 
    ## Final Model:
    ## RenewableGeneration_Geothermal ~ humidity + temp + rain_1h + 
    ##     directnormalirradiance + globalhorizontalirradiance_2 + Hour + 
    ##     Month
    ## 
    ## 
    ##                              Step Df     Deviance Resid. Df Resid. Dev
    ## 1                                                       211 0.03091131
    ## 2                    - wind_speed  1 1.973355e-06       212 0.03091328
    ## 3                       - snow_1h  1 3.401364e-06       213 0.03091668
    ## 4                      - wind_deg  1 4.213945e-05       214 0.03095882
    ## 5   - diffusehorizontalirradiance  1 5.665564e-05       215 0.03101548
    ## 6      - directnormalirradiance_2  1 1.180027e-04       216 0.03113348
    ## 7 - diffusehorizontalirradiance_2  1 2.042033e-04       217 0.03133768
    ##         AIC
    ## 1 -1444.592
    ## 2 -1446.576
    ## 3 -1448.549
    ## 4 -1450.212
    ## 5 -1451.761
    ## 6 -1452.823
    ## 7 -1453.208

    LSr_geo <- glm(formula(step_geo),data=train_geo)
    pred <- predict(LSr_geo,test_x_geo)
    MSE_geor <- mean((pred-test_y_geo)^2)
    print(c(MSE_geo,MSE_geor))

    ## [1] 2.5321314329 0.0002048967

    # hydro 
    # LS
    LS_hydro <- glm(RenewableGeneration_Hydro~.,data=train_hydro)
    summary(LS_hydro)

    ## 
    ## Call:
    ## glm(formula = RenewableGeneration_Hydro ~ ., data = train_hydro)
    ## 
    ## Deviance Residuals: 
    ##     Min       1Q   Median       3Q      Max  
    ## -3.2715  -0.5237  -0.0066   0.5417   2.3268  
    ## 
    ## Coefficients:
    ##                                 Estimate Std. Error t value Pr(>|t|)    
    ## (Intercept)                     8.200881   1.656300   4.951 1.51e-06 ***
    ## humidity                       -0.023902   0.015202  -1.572 0.117370    
    ## temp                           -0.160851   0.051525  -3.122 0.002050 ** 
    ## rain_1h                         1.056686   0.364945   2.895 0.004184 ** 
    ## snow_1h                         0.155261   6.139780   0.025 0.979849    
    ## wind_deg                       -0.002406   0.002744  -0.877 0.381666    
    ## wind_speed                      0.110557   0.120986   0.914 0.361864    
    ## directnormalirradiance         -0.002990   0.001030  -2.903 0.004094 ** 
    ## diffusehorizontalirradiance    -0.006033   0.005556  -1.086 0.278721    
    ## globalhorizontalirradiance_2    0.056451   0.022748   2.482 0.013861 *  
    ## directnormalirradiance_2       -0.042932   0.050338  -0.853 0.394687    
    ## diffusehorizontalirradiance_2   0.426923   0.571096   0.748 0.455563    
    ## Hour1                          -0.249551   0.381343  -0.654 0.513566    
    ## Hour2                          -0.457550   0.423320  -1.081 0.280993    
    ## Hour3                          -0.549925   0.410489  -1.340 0.181790    
    ## Hour4                          -0.487218   0.426221  -1.143 0.254287    
    ## Hour5                          -4.451920   4.177123  -1.066 0.287738    
    ## Hour6                         -12.232399   5.273513  -2.320 0.021319 *  
    ## Hour7                         -23.001290   6.993493  -3.289 0.001178 ** 
    ## Hour8                         -34.281666   8.697183  -3.942 0.000110 ***
    ## Hour9                         -46.084646  10.170920  -4.531 9.82e-06 ***
    ## Hour10                        -54.697691  11.282601  -4.848 2.42e-06 ***
    ## Hour11                        -59.754726  11.923825  -5.011 1.14e-06 ***
    ## Hour12                        -60.871041  11.993835  -5.075 8.48e-07 ***
    ## Hour13                        -57.593831  11.474919  -5.019 1.10e-06 ***
    ## Hour14                        -50.997200  10.492586  -4.860 2.29e-06 ***
    ## Hour15                        -41.322948   9.073085  -4.554 8.88e-06 ***
    ## Hour16                        -28.537362   7.370317  -3.872 0.000144 ***
    ## Hour17                        -15.358927   5.635590  -2.725 0.006963 ** 
    ## Hour18                         -3.875091   4.256455  -0.910 0.363649    
    ## Hour19                          3.207028   0.592993   5.408 1.72e-07 ***
    ## Hour20                          4.510478   0.439379  10.266  < 2e-16 ***
    ## Hour21                          3.285562   0.397793   8.259 1.60e-14 ***
    ## Hour22                          1.682337   0.425617   3.953 0.000105 ***
    ## Hour23                          1.003689   0.412954   2.431 0.015913 *  
    ## Month05                         0.123783   0.231810   0.534 0.593913    
    ## ---
    ## Signif. codes:  0 '***' 0.001 '**' 0.01 '*' 0.05 '.' 0.1 ' ' 1
    ## 
    ## (Dispersion parameter for gaussian family taken to be 0.9390124)
    ## 
    ##     Null deviance: 816.04  on 246  degrees of freedom
    ## Residual deviance: 198.13  on 211  degrees of freedom
    ## AIC: 720.5
    ## 
    ## Number of Fisher Scoring iterations: 2

    pred <- predict(LS_hydro,test_x_hydro)
    MSE_hydro <- mean((pred-test_y_hydro)^2)
    # reduced
    step_hydro <- stepAIC(LS_hydro, direction = "both",trace = F)
    step_hydro$anova

    ## Stepwise Model Path 
    ## Analysis of Deviance Table
    ## 
    ## Initial Model:
    ## RenewableGeneration_Hydro ~ humidity + temp + rain_1h + snow_1h + 
    ##     wind_deg + wind_speed + directnormalirradiance + diffusehorizontalirradiance + 
    ##     globalhorizontalirradiance_2 + directnormalirradiance_2 + 
    ##     diffusehorizontalirradiance_2 + Hour + Month
    ## 
    ## Final Model:
    ## RenewableGeneration_Hydro ~ humidity + temp + rain_1h + directnormalirradiance + 
    ##     globalhorizontalirradiance_2 + Hour
    ## 
    ## 
    ##                              Step Df     Deviance Resid. Df Resid. Dev      AIC
    ## 1                                                       211   198.1316 720.5028
    ## 2                       - snow_1h  1 0.0006004683       212   198.1322 718.5036
    ## 3                         - Month  1 0.2744714770       213   198.4067 716.8455
    ## 4 - diffusehorizontalirradiance_2  1 0.6544674737       214   199.0612 715.6589
    ## 5      - directnormalirradiance_2  1 0.5945693920       215   199.6557 714.3956
    ## 6                      - wind_deg  1 0.5887662511       216   200.2445 713.1229
    ## 7                    - wind_speed  1 0.4617888612       217   200.7063 711.6918
    ## 8   - diffusehorizontalirradiance  1 1.5122653640       218   202.2185 711.5459

    LSr_hydro <- glm(formula(step_hydro),data=train_hydro)
    pred <- predict(LSr_hydro,test_x_hydro)
    MSE_hydror <- mean((pred-test_y_hydro)^2)
    print(c(MSE_hydro,MSE_hydror))

    ## [1] 0.9437221 0.9454158

    # photovoltaic
    # LS 
    LS_photo <- glm(RenewableGeneration_Photovoltaic~.,data=train_photo)
    summary(LS_photo)

    ## 
    ## Call:
    ## glm(formula = RenewableGeneration_Photovoltaic ~ ., data = train_photo)
    ## 
    ## Deviance Residuals: 
    ##      Min        1Q    Median        3Q       Max  
    ## -2.31867  -0.38026  -0.01826   0.46512   1.96198  
    ## 
    ## Coefficients:
    ##                                 Estimate Std. Error t value Pr(>|t|)    
    ## (Intercept)                    4.308e+00  1.383e+00   3.116  0.00209 ** 
    ## humidity                      -7.149e-02  1.226e-02  -5.831 2.04e-08 ***
    ## temp                           1.053e-01  4.118e-02   2.558  0.01123 *  
    ## rain_1h                       -1.277e+00  3.174e-01  -4.024 7.98e-05 ***
    ## snow_1h                       -1.781e+02  1.328e+02  -1.341  0.18149    
    ## wind_deg                       4.151e-03  2.399e-03   1.730  0.08504 .  
    ## wind_speed                    -5.864e-02  1.009e-01  -0.581  0.56153    
    ## directnormalirradiance         7.435e-03  7.838e-04   9.485  < 2e-16 ***
    ## diffusehorizontalirradiance    2.658e-02  4.077e-03   6.518 5.17e-10 ***
    ## globalhorizontalirradiance_2  -4.803e-02  1.916e-02  -2.507  0.01292 *  
    ## directnormalirradiance_2      -9.093e-02  4.097e-02  -2.219  0.02752 *  
    ## diffusehorizontalirradiance_2  9.257e-01  4.704e-01   1.968  0.05038 .  
    ## Hour1                          1.033e-01  3.783e-01   0.273  0.78510    
    ## Hour2                          1.727e-01  4.003e-01   0.431  0.66656    
    ## Hour3                          3.024e-01  3.808e-01   0.794  0.42811    
    ## Hour4                          3.231e-01  3.672e-01   0.880  0.37989    
    ## Hour5                         -3.607e+00  3.555e+00  -1.015  0.31142    
    ## Hour6                         -1.568e-01  4.500e+00  -0.035  0.97223    
    ## Hour7                          3.335e+00  5.789e+00   0.576  0.56512    
    ## Hour8                          7.866e+00  7.126e+00   1.104  0.27088    
    ## Hour9                          1.149e+01  8.259e+00   1.391  0.16576    
    ## Hour10                         1.473e+01  9.106e+00   1.618  0.10724    
    ## Hour11                         1.687e+01  9.607e+00   1.756  0.08051 .  
    ## Hour12                         1.685e+01  9.656e+00   1.745  0.08246 .  
    ## Hour13                         1.547e+01  9.273e+00   1.669  0.09668 .  
    ## Hour14                         1.497e+01  8.503e+00   1.760  0.07982 .  
    ## Hour15                         1.163e+01  7.413e+00   1.569  0.11810    
    ## Hour16                         8.019e+00  6.108e+00   1.313  0.19070    
    ## Hour17                         4.068e+00  4.784e+00   0.850  0.39610    
    ## Hour18                        -1.217e+00  3.639e+00  -0.335  0.73831    
    ## Hour19                        -1.148e+00  5.409e-01  -2.123  0.03495 *  
    ## Hour20                        -5.414e-01  3.496e-01  -1.549  0.12298    
    ## Hour21                        -3.693e-01  3.604e-01  -1.025  0.30670    
    ## Hour22                        -3.633e-01  3.790e-01  -0.959  0.33880    
    ## Hour23                         7.066e-03  3.580e-01   0.020  0.98427    
    ## Month05                       -4.098e-01  2.034e-01  -2.015  0.04516 *  
    ## ---
    ## Signif. codes:  0 '***' 0.001 '**' 0.01 '*' 0.05 '.' 0.1 ' ' 1
    ## 
    ## (Dispersion parameter for gaussian family taken to be 0.6311145)
    ## 
    ##     Null deviance: 4919.06  on 246  degrees of freedom
    ## Residual deviance:  133.17  on 211  degrees of freedom
    ## AIC: 622.36
    ## 
    ## Number of Fisher Scoring iterations: 2

    pred <- predict(LS_photo,test_x_photo)
    MSE_photo <- mean((pred-test_y_photo)^2)
    # reduced
    step_photo <- stepAIC(LS_photo, direction = "both",trace = F)
    step_photo$anova

    ## Stepwise Model Path 
    ## Analysis of Deviance Table
    ## 
    ## Initial Model:
    ## RenewableGeneration_Photovoltaic ~ humidity + temp + rain_1h + 
    ##     snow_1h + wind_deg + wind_speed + directnormalirradiance + 
    ##     diffusehorizontalirradiance + globalhorizontalirradiance_2 + 
    ##     directnormalirradiance_2 + diffusehorizontalirradiance_2 + 
    ##     Hour + Month
    ## 
    ## Final Model:
    ## RenewableGeneration_Photovoltaic ~ humidity + temp + rain_1h + 
    ##     snow_1h + wind_deg + directnormalirradiance + diffusehorizontalirradiance + 
    ##     globalhorizontalirradiance_2 + directnormalirradiance_2 + 
    ##     diffusehorizontalirradiance_2 + Hour + Month
    ## 
    ## 
    ##           Step Df  Deviance Resid. Df Resid. Dev      AIC
    ## 1                                 211   133.1652 622.3595
    ## 2 - wind_speed  1 0.2133953       212   133.3786 620.7550

    LSr_photo <- glm(formula(step_photo), data=train_photo)
    pred <- predict(LSr_photo,test_x_photo)
    MSE_photor <- mean((pred-test_y_photo)^2)
    print(c(MSE_photo,MSE_photor))

    ## [1]  9.767496 11.429402

    # wind
    # LS
    LS_wind <- glm(RenewableGeneration_Wind~.,data=train_wind)
    summary(LS_wind)

    ## 
    ## Call:
    ## glm(formula = RenewableGeneration_Wind ~ ., data = train_wind)
    ## 
    ## Deviance Residuals: 
    ##      Min        1Q    Median        3Q       Max  
    ## -2.72088  -0.59562   0.00742   0.60695   2.39665  
    ## 
    ## Coefficients:
    ##                                Estimate Std. Error t value Pr(>|t|)    
    ## (Intercept)                   -2.268645   1.876006  -1.209 0.227903    
    ## humidity                       0.015158   0.016237   0.933 0.351631    
    ## temp                          -0.011521   0.055090  -0.209 0.834546    
    ## rain_1h                        0.044927   0.376118   0.119 0.905032    
    ## snow_1h                       11.816455  19.109697   0.618 0.537012    
    ## wind_deg                       0.004215   0.002914   1.446 0.149562    
    ## wind_speed                     0.937710   0.132252   7.090 1.98e-11 ***
    ## directnormalirradiance        -0.001524   0.001153  -1.322 0.187528    
    ## diffusehorizontalirradiance   -0.003259   0.005940  -0.549 0.583811    
    ## globalhorizontalirradiance_2   0.087542   0.026737   3.274 0.001238 ** 
    ## directnormalirradiance_2       0.150387   0.058895   2.553 0.011372 *  
    ## diffusehorizontalirradiance_2 -1.823175   0.682903  -2.670 0.008182 ** 
    ## Hour1                          0.086414   0.440464   0.196 0.844651    
    ## Hour2                          0.049047   0.463859   0.106 0.915892    
    ## Hour3                          0.260892   0.432718   0.603 0.547214    
    ## Hour4                          0.257499   0.454318   0.567 0.571466    
    ## Hour5                         13.297632   5.143031   2.586 0.010395 *  
    ## Hour6                         11.697468   6.383362   1.832 0.068287 .  
    ## Hour7                         10.456143   8.299170   1.260 0.209096    
    ## Hour8                          7.120564  10.150438   0.702 0.483762    
    ## Hour9                          3.601181  11.656673   0.309 0.757674    
    ## Hour10                         0.041917  12.801207   0.003 0.997390    
    ## Hour11                        -1.454512  13.444833  -0.108 0.913953    
    ## Hour12                        -1.863892  13.497837  -0.138 0.890302    
    ## Hour13                        -0.484028  12.995748  -0.037 0.970325    
    ## Hour14                         1.933385  12.015925   0.161 0.872325    
    ## Hour15                         5.638018  10.547525   0.535 0.593534    
    ## Hour16                         9.145279   8.771917   1.043 0.298344    
    ## Hour17                        11.432566   6.829832   1.674 0.095629 .  
    ## Hour18                        12.132032   5.255850   2.308 0.021952 *  
    ## Hour19                         0.760964   0.700732   1.086 0.278738    
    ## Hour20                        -0.300630   0.452521  -0.664 0.507196    
    ## Hour21                        -0.306267   0.456957  -0.670 0.503443    
    ## Hour22                        -0.302881   0.450676  -0.672 0.502280    
    ## Hour23                         0.329557   0.463799   0.711 0.478142    
    ## Month05                        0.934867   0.261396   3.576 0.000432 ***
    ## ---
    ## Signif. codes:  0 '***' 0.001 '**' 0.01 '*' 0.05 '.' 0.1 ' ' 1
    ## 
    ## (Dispersion parameter for gaussian family taken to be 1.093582)
    ## 
    ##     Null deviance: 508.71  on 246  degrees of freedom
    ## Residual deviance: 230.75  on 211  degrees of freedom
    ## AIC: 758.14
    ## 
    ## Number of Fisher Scoring iterations: 2

    pred <- predict(LS_wind,test_x_wind)
    MSE_wind <- mean((pred-test_y_wind)^2)
    print(MSE_wind)

    ## [1] 0.8401228

    # reduced
    step_wind <- stepAIC(LS_wind, direction = "both",trace = F)
    step_wind$anova

    ## Stepwise Model Path 
    ## Analysis of Deviance Table
    ## 
    ## Initial Model:
    ## RenewableGeneration_Wind ~ humidity + temp + rain_1h + snow_1h + 
    ##     wind_deg + wind_speed + directnormalirradiance + diffusehorizontalirradiance + 
    ##     globalhorizontalirradiance_2 + directnormalirradiance_2 + 
    ##     diffusehorizontalirradiance_2 + Hour + Month
    ## 
    ## Final Model:
    ## RenewableGeneration_Wind ~ humidity + wind_deg + wind_speed + 
    ##     diffusehorizontalirradiance_2 + Month
    ## 
    ## 
    ##                             Step Df    Deviance Resid. Df Resid. Dev      AIC
    ## 1                                                     211   230.7459 758.1420
    ## 2                         - Hour 23 23.58167459       234   254.3276 736.1766
    ## 3                         - temp  1  0.05513864       235   254.3827 734.2302
    ## 4                      - rain_1h  1  0.08935759       236   254.4721 732.3169
    ## 5       - directnormalirradiance  1  0.07676717       237   254.5488 730.3914
    ## 6  - diffusehorizontalirradiance  1  0.02510296       238   254.5739 728.4158
    ## 7                      - snow_1h  1  0.63367502       239   255.2076 727.0298
    ## 8 - globalhorizontalirradiance_2  1  0.85388289       240   256.0615 725.8549
    ## 9     - directnormalirradiance_2  1  1.03838557       241   257.0999 724.8545

    LSr_wind <- glm(formula(step_wind), data=train_wind)
    pred <- predict(LSr_wind,test_x_wind)
    MSE_windr <- mean((pred-test_y_wind)^2)
    print(c(MSE_wind,MSE_windr))

    ## [1] 0.8401228 0.7970247

    library(ggplot2)
    library(ggthemes)
    library(gridExtra)
    library(patchwork)
    MSE_value = c(MSE_bio,MSE_geo,MSE_hydro,MSE_photo,MSE_wind)
    tmp <- data.frame(Energy= c("biomass","geothermal","hydro","photovoltaic","wind"), MSE_value = c(MSE_bio,MSE_geo,MSE_hydro,MSE_photo,MSE_wind))
    print(tmp)

    ##         Energy MSE_value
    ## 1      biomass 0.1139999
    ## 2   geothermal 2.5321314
    ## 3        hydro 0.9437221
    ## 4 photovoltaic 9.7674955
    ## 5         wind 0.8401228

    plot1 <- ggplot(data=tmp, aes(x=Energy, y=MSE_value, fill=MSE_value))+
      geom_histogram(stat="identity")+ theme_tufte()+ggtitle("MSE ~ energy source")+
      theme(legend.position="none")+ylim(0,12)
    tmp <- data.frame(Energy= c("biomass","geothermal","hydro","photovoltaic","wind"), MSE_value_r = c(MSE_bior,MSE_geor,MSE_hydror,MSE_photor,MSE_windr))
    plot2 <- ggplot(data=tmp, aes(x=Energy, y=MSE_value_r, fill=MSE_value))+
      geom_histogram(stat="identity")+ theme_tufte()+ggtitle("MSE ~ energy source - reduced models")+
      theme(legend.position="none")+ylim(0,12)
    plot1 + plot2

![](energy_production_files/figure-markdown_strict/unnamed-chunk-13-1.png)

    # non linear - random forests
    # biomass
    library(randomForest)
    set.seed(25)
    p = ncol(biomass)-1
    m = (p/3)
    MSE_biomass <- c()
    forest <- randomForest(RenewableGeneration_Biomass~.,data=train_bio, mtry=m)
    forestr <- randomForest(formula(step_bio),data=train_bio, mtry=m)
    pred_forest <- predict(forest, test_x_bio)
    pred_forestr <- predict(forestr, test_x_bio)
    MSE_bio_forest <- mean((test_y_bio-pred_forest)^2)
    MSE_bio_forestr <- mean((test_y_bio-pred_forestr)^2)
    MSE_biomass <- append(MSE_biomass, c(MSE_bio,MSE_bior,MSE_bio_forest,MSE_bio_forestr))
    print(MSE_biomass)

    ## [1] 0.11399994 0.11211285 0.08084189 0.10198634

    set.seed(25)
    p = ncol(geothermal)-1
    m = (p/3)
    MSE_geothermal <- c()
    forest <- randomForest(RenewableGeneration_Geothermal~.,data=train_geo, mtry=m)
    forestr <- randomForest(formula(step_geo),data=train_geo, mtry=m)
    pred_forest <- predict(forest, test_x_geo)
    pred_forestr <- predict(forestr, test_x_geo)
    MSE_geo_forest <- mean((test_y_bio-pred_forest)^2)
    MSE_geo_forestr <- mean((test_y_bio-pred_forestr)^2)
    MSE_geothermal <- append(MSE_geothermal, c(MSE_geo,MSE_geor,MSE_geo_forest,MSE_geo_forestr))
    print(MSE_geothermal)

    ## [1] 2.5321314329 0.0002048967 2.5619669802 2.5618756254

    set.seed(25)
    p = ncol(hydro)-1
    m = (p/3)
    MSE_hydroelectric <- c()
    forest <- randomForest(RenewableGeneration_Hydro~.,data=train_hydro, mtry=m)
    forestr <- randomForest(formula(step_hydro),data=train_hydro, mtry=m)
    pred_forest <- predict(forest, test_x_hydro)
    pred_forestr <- predict(forestr, test_x_hydro)
    MSE_hydro_forest <- mean((test_y_hydro-pred_forest)^2)
    MSE_hydro_forestr <- mean((test_y_hydro-pred_forestr)^2)
    MSE_hydroelectric <- append(MSE_hydroelectric, c(MSE_hydro,MSE_hydror,MSE_hydro_forest,MSE_hydro_forestr))
    print(MSE_hydroelectric)

    ## [1] 0.9437221 0.9454158 0.9957821 0.9376167

    set.seed(25)
    p = ncol(photovoltaic)-1
    m = (p/3)
    MSE_photovoltaic <- c()
    forest <- randomForest(RenewableGeneration_Photovoltaic~.,data=train_photo, mtry=m)
    forestr <- randomForest(formula(step_photo),data=train_photo, mtry=m)
    pred_forest <- predict(forest, test_x_photo)
    pred_forestr <- predict(forestr, test_x_photo)
    MSE_photo_forest <- mean((test_y_photo-pred_forest)^2)
    MSE_photo_forestr <- mean((test_y_photo-pred_forestr)^2)
    MSE_photovoltaic <- append(MSE_photovoltaic, c(MSE_photo,MSE_photor,MSE_photo_forest,MSE_photo_forestr))
    print(MSE_photovoltaic)

    ## [1]  9.7674955 11.4294017  0.5543723  0.5698644

    set.seed(25)
    p = ncol(wind)-1
    m = (p/3)
    MSE_Wind <- c()
    forest <- randomForest(RenewableGeneration_Wind~.,data=train_wind, mtry=m)
    forestr <- randomForest(formula(step_wind),data=train_wind, mtry=m)
    pred_forest <- predict(forest, test_x_wind)
    pred_forestr <- predict(forestr, test_x_wind)
    MSE_wind_forest <- mean((test_y_wind-pred_forest)^2)
    MSE_wind_forestr <- mean((test_y_wind-pred_forestr)^2)
    MSE_Wind <- append(MSE_Wind, c(MSE_wind,MSE_windr,MSE_wind_forest,MSE_wind_forestr))
    print(MSE_Wind)

    ## [1] 0.8401228 0.7970247 0.6706659 0.8396899

    MSE_table <- data.frame(MSE_biomass,MSE_geothermal,MSE_hydroelectric,MSE_photovoltaic,MSE_Wind, row.names = c("LS Regression","Reduced LS Regression","RandomForests","Reduced RandomForests"))
    print(MSE_table)

    ##                       MSE_biomass MSE_geothermal MSE_hydroelectric
    ## LS Regression          0.11399994   2.5321314329         0.9437221
    ## Reduced LS Regression  0.11211285   0.0002048967         0.9454158
    ## RandomForests          0.08084189   2.5619669802         0.9957821
    ## Reduced RandomForests  0.10198634   2.5618756254         0.9376167
    ##                       MSE_photovoltaic  MSE_Wind
    ## LS Regression                9.7674955 0.8401228
    ## Reduced LS Regression       11.4294017 0.7970247
    ## RandomForests                0.5543723 0.6706659
    ## Reduced RandomForests        0.5698644 0.8396899

    b <- rownames(MSE_table)[MSE_biomass==min(MSE_biomass)]
    g <- rownames(MSE_table)[MSE_geothermal==min(MSE_geothermal)]
    h <- rownames(MSE_table)[MSE_hydroelectric==min(MSE_hydroelectric)]
    p <- rownames(MSE_table)[MSE_photovoltaic==min(MSE_photovoltaic)]
    w <- rownames(MSE_table)[MSE_Wind==min(MSE_Wind)]

Optimal models: - biomass: RandomForests - geothermal: reduced LS
regression - hydroelectric: reduced RandomForests - photovoltaic:
RandomForests - wind: RandomForests

    opt <- data.frame(Energy= c("biomass","geothermal","hydro","photovoltaic","wind"),OptimModel=c(b,g,h,p,w), OptimMSE=c(min(MSE_biomass),min(MSE_geothermal),min(MSE_hydroelectric),min(MSE_photovoltaic),min(MSE_Wind)))
    print(opt)

    ##         Energy            OptimModel     OptimMSE
    ## 1      biomass         RandomForests 0.0808418915
    ## 2   geothermal Reduced LS Regression 0.0002048967
    ## 3        hydro Reduced RandomForests 0.9376167053
    ## 4 photovoltaic         RandomForests 0.5543722610
    ## 5         wind         RandomForests 0.6706658526

    library(patchwork)
    tmp <- data.frame(Energy= c("biomass","geothermal","hydro","photovoltaic","wind"), LS_MSE=c(MSE_biomass[1],MSE_geothermal[1],MSE_hydroelectric[1],MSE_photovoltaic[1],MSE_Wind[1]),RandomForest_MSE=c(MSE_biomass[3],MSE_geothermal[3],MSE_hydroelectric[3],MSE_photovoltaic[3],MSE_Wind[3]))
    print(tmp)

    ##         Energy    LS_MSE RandomForest_MSE
    ## 1      biomass 0.1139999       0.08084189
    ## 2   geothermal 2.5321314       2.56196698
    ## 3        hydro 0.9437221       0.99578209
    ## 4 photovoltaic 9.7674955       0.55437226
    ## 5         wind 0.8401228       0.67066585

    plot1 <- ggplot(data=tmp, aes(x=Energy, y=LS_MSE, fill=LS_MSE))+
      geom_histogram(stat="identity")+ theme_tufte()+ggtitle("MSE ~ energy source - LS")+
      theme(legend.position="none")+ylim(0,12)
    plot2 <- ggplot(data=tmp, aes(x=Energy, y=RandomForest_MSE, fill=LS_MSE))+
      geom_histogram(stat="identity")+ theme_tufte()+ggtitle("MSE ~ energy source - RandomForest")+
      theme(legend.position="none")+ylim(0,12)
    plot1 + plot2

![](energy_production_files/figure-markdown_strict/unnamed-chunk-21-1.png)

    biomass_p <- attr(terms(step_bio), "term.labels")
    print(biomass_p, justify="col")

    ## [1] "temp"                          "rain_1h"                      
    ## [3] "globalhorizontalirradiance_2"  "directnormalirradiance_2"     
    ## [5] "diffusehorizontalirradiance_2" "Hour"                         
    ## [7] "Month"

    geo_p <- attr(terms(step_geo), "term.labels")
    print(geo_p)

    ## [1] "humidity"                     "temp"                        
    ## [3] "rain_1h"                      "directnormalirradiance"      
    ## [5] "globalhorizontalirradiance_2" "Hour"                        
    ## [7] "Month"

    hydro_p <- attr(terms(step_hydro), "term.labels")
    print(hydro_p)

    ## [1] "humidity"                     "temp"                        
    ## [3] "rain_1h"                      "directnormalirradiance"      
    ## [5] "globalhorizontalirradiance_2" "Hour"

    photo_p <- attr(terms(step_photo), "term.labels")
    print(photo_p)

    ##  [1] "humidity"                      "temp"                         
    ##  [3] "rain_1h"                       "snow_1h"                      
    ##  [5] "wind_deg"                      "directnormalirradiance"       
    ##  [7] "diffusehorizontalirradiance"   "globalhorizontalirradiance_2" 
    ##  [9] "directnormalirradiance_2"      "diffusehorizontalirradiance_2"
    ## [11] "Hour"                          "Month"

    wind_p <- attr(terms(step_wind), "term.labels")
    print(wind_p)

    ## [1] "humidity"                      "wind_deg"                     
    ## [3] "wind_speed"                    "diffusehorizontalirradiance_2"
    ## [5] "Month"
