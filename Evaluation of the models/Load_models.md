Load
================
Gabriele
2/5/2021

This notebook is made to understand how to predict the total load in
italy. We basically start from some exploratory analysis and then we
will look for the optimal model, after that we will implement that model
into python.

> ### 1\) Exploratory analisys

``` r
load <- read.csv("ao.csv")[c(-1,-5,-2)]
load$Holiday <- factor(load$Holiday)
load$Hours <- factor(load$Hours)
load$Month <- factor(load$Month)
str(load)
```

    ## 'data.frame':    55384 obs. of  4 variables:
    ##  $ Load   : num  24357 24091 23842 23632 23502 ...
    ##  $ Hours  : Factor w/ 24 levels "0","1","2","3",..: 1 1 1 1 2 2 2 2 3 3 ...
    ##  $ Month  : Factor w/ 12 levels "April","August",..: 5 5 5 5 5 5 5 5 5 5 ...
    ##  $ Holiday: Factor w/ 3 levels "half","no","yes": 3 3 3 3 3 3 3 3 3 3 ...

Let’s see some details of Load related to the other variables:

``` r
library(pander)

x <- data.frame(aggregate(Load~Holiday, data=load, FUN =mean)) 
pander(x,justify = "center")
```

| Holiday | Load  |
| :-----: | :---: |
|  half   | 30747 |
|   no    | 36755 |
|   yes   | 28274 |

Let’s also have a graphical representation of those data:

``` r
library(ggplot2)
library(ggthemes)
ggplot(data=load, aes(x=Holiday, y=Load, fill=Holiday))+
  geom_boxplot()+theme_tufte()+ggtitle("Boxplot Load ~ Holiday")+
  theme(legend.position = "top")
```

<img src="Load_models_files/figure-gfm/unnamed-chunk-3-1.png" style="display: block; margin: auto;" />

``` r
library(gridExtra)
g1<-ggplot(data=load[load$Holiday=="no",], aes(x=Hours, y=Load, fill=Hours))+
  geom_boxplot()+theme_tufte()+ggtitle("Load ~ Hours when holiday = no ")+
  theme(legend.position = "none")

g2<-ggplot(data=load[load$Holiday=="yes",], aes(x=Hours, y=Load, fill=Hours))+
  geom_boxplot()+theme_tufte()+ggtitle("Load ~ Hours when holiday = yes")+
  theme(legend.position = "none")

g3<-ggplot(data=load[load$Holiday=="half",], aes(x=Hours, y=Load, fill=Hours))+
  geom_boxplot()+theme_tufte()+ggtitle("Load ~ Hours when holiday = half ")+
  theme(legend.position = "none")

g1
```

<img src="Load_models_files/figure-gfm/unnamed-chunk-4-1.png" style="display: block; margin: auto;" />

``` r
g2
```

<img src="Load_models_files/figure-gfm/unnamed-chunk-5-1.png" style="display: block; margin: auto;" />

``` r
g3
```

<img src="Load_models_files/figure-gfm/unnamed-chunk-6-1.png" style="display: block; margin: auto;" />

> ### Linear Regression

``` r
set.seed(42)
r <- sample(nrow(load), nrow(load)*0.33)
train <- load[-r,]
test_x <- load[r,-1]
test_y <- load[r,1]
reg1 <- glm(Load ~ ., data=train)
(summary(reg1))
```

    ## 
    ## Call:
    ## glm(formula = Load ~ ., data = train)
    ## 
    ## Deviance Residuals: 
    ##      Min        1Q    Median        3Q       Max  
    ## -18696.7   -2395.2     206.7    2533.1   15902.4  
    ## 
    ## Coefficients:
    ##                Estimate Std. Error t value Pr(>|t|)    
    ## (Intercept)    16687.92     127.66  130.72   <2e-16 ***
    ## Hours1         -1851.38     141.88  -13.05   <2e-16 ***
    ## Hours2         -2729.22     141.83  -19.24   <2e-16 ***
    ## Hours3         -2952.66     141.86  -20.81   <2e-16 ***
    ## Hours4         -2881.49     141.29  -20.39   <2e-16 ***
    ## Hours5         -1572.69     142.03  -11.07   <2e-16 ***
    ## Hours6          1961.62     141.53   13.86   <2e-16 ***
    ## Hours7          6291.14     141.68   44.40   <2e-16 ***
    ## Hours8         10285.30     141.20   72.84   <2e-16 ***
    ## Hours9         12154.48     141.84   85.69   <2e-16 ***
    ## Hours10        12471.27     140.86   88.54   <2e-16 ***
    ## Hours11        12594.41     141.52   89.00   <2e-16 ***
    ## Hours12        11282.29     142.31   79.28   <2e-16 ***
    ## Hours13        10679.74     141.75   75.34   <2e-16 ***
    ## Hours14        10861.44     141.15   76.95   <2e-16 ***
    ## Hours15        10939.57     141.91   77.09   <2e-16 ***
    ## Hours16        11016.98     141.77   77.71   <2e-16 ***
    ## Hours17        11587.19     142.31   81.42   <2e-16 ***
    ## Hours18        12278.73     140.86   87.17   <2e-16 ***
    ## Hours19        12935.39     141.33   91.53   <2e-16 ***
    ## Hours20        11676.35     141.24   82.67   <2e-16 ***
    ## Hours21         9177.00     140.55   65.29   <2e-16 ***
    ## Hours22         5719.10     142.03   40.27   <2e-16 ***
    ## Hours23         2676.96     141.91   18.86   <2e-16 ***
    ## MonthAugust     8015.94     109.00   73.54   <2e-16 ***
    ## MonthDecember   7032.54     108.55   64.78   <2e-16 ***
    ## MonthFebruary   9745.50      82.76  117.76   <2e-16 ***
    ## MonthJanuary    9659.55      81.78  118.11   <2e-16 ***
    ## MonthJuly      11152.04     108.01  103.25   <2e-16 ***
    ## MonthJune       6018.56     109.90   54.76   <2e-16 ***
    ## MonthMarch      5754.92      81.62   70.51   <2e-16 ***
    ## MonthMay        3043.82     108.65   28.01   <2e-16 ***
    ## MonthNovember   7958.44     110.72   71.88   <2e-16 ***
    ## MonthOctober    7598.70     108.85   69.81   <2e-16 ***
    ## MonthSeptember  9129.60     110.36   82.73   <2e-16 ***
    ## Holidayno       6154.93      60.05  102.49   <2e-16 ***
    ## Holidayyes     -2588.14      74.98  -34.52   <2e-16 ***
    ## ---
    ## Signif. codes:  0 '***' 0.001 '**' 0.01 '*' 0.05 '.' 0.1 ' ' 1
    ## 
    ## (Dispersion parameter for gaussian family taken to be 15528865)
    ## 
    ##     Null deviance: 2.6438e+12  on 37107  degrees of freedom
    ## Residual deviance: 5.7567e+11  on 37071  degrees of freedom
    ## AIC: 719789
    ## 
    ## Number of Fisher Scoring iterations: 2

  - MSE:

<!-- end list -->

``` r
pred <- predict(reg1, test_x)
MSE_LM <- mean((test_y-pred)^2)
print(MSE_LM)
```

    ## [1] 15431269

> ### Linear Regression with interaction terms:

``` r
reg2 <- glm(Load ~ Month*Hours+Holiday, data=train)
```

  - MSE:

<!-- end list -->

``` r
pred <- predict(reg2, test_x)
MSE_LM_interaction <- mean((test_y-pred)^2)
print(MSE_LM_interaction)
```

    ## [1] 13928483

> ### RandomForest

  - Since the problems is non linear we will use models that perform
    better in this situation as the randomForest\!

<!-- end list -->

``` r
library(randomForest)
MSE_randomForest <- c()
forest <- randomForest(Load~., data=train, ntree=250, mtry=2)
pred_forest <- predict(forest, test_x)
MSE_Forest <- mean((test_y-pred_forest)^2)
MSE_randomForest <- append(MSE_randomForest, MSE_Forest)
print(MSE_randomForest)
```

    ## [1] 9903950

> ### Comparision of the models:

``` r
tmp <- data.frame(MSE= c(MSE_LM_interaction, MSE_LM, min(MSE_randomForest)),
                  Model = c('Linear_with_interaction', 'Linear', 'RandomForest'))
ggplot(data=tmp, aes(x=Model, y=MSE, fill=MSE))+
  geom_histogram(stat="identity")+ theme_tufte()+ggtitle("MSE ~ Models")+
  theme(legend.position="none")
```

<img src="Load_models_files/figure-gfm/unnamed-chunk-12-1.png" style="display: block; margin: auto;" />
