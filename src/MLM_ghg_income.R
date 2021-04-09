#######################################################
## Workshop 2: random slopes / random effects models ##
#######################################################

rm(list=ls())
list_of_packages <- c("ggplot2","MASS","reshape","lme4", "summarytools", "doBy", "gridExtra")
new_packages <- list_of_packages[!(list_of_packages %in% installed.packages()[,"Package"])]
if(length(new_packages)) install.packages(new_packages)
for (i in 1:length(list_of_packages))
{
  require(list_of_packages[i],character.only = T)
}

library(tidyverse)

## Load long data income and emissions data
MyData <- read.csv("data/processed/modelling_data.csv")

# plot the longitudinal BMI data by Sex 4 ways: loess, cubic, quadratic, linear
#p1 <- ggplot(aes(x=income, y=total_ghg, group=year_str, colour=year_str), data=MyData) + geom_smooth(method="loess", formula = y ~ x, se=TRUE)
#p2 <- ggplot(aes(x=income, y=total_ghg, group=year_str, colour=year_str), data=MyData) + geom_smooth(method="lm", formula = y ~ poly(x,3), se=FALSE)
#p3 <- ggplot(aes(x=income, y=total_ghg, group=year_str, colour=year_str), data=MyData) + geom_smooth(method="lm", formula = y ~ poly(x,2), se=FALSE)
#p4 <- 
ggplot(aes(x=income, y=total_ghg, group=year_str, colour=year_str), data=MyData) + 
  geom_smooth(method="lm", formula = y ~ poly(x,1), se=FALSE)

ggplot(aes(x=total_ghg, group=year_str, fill=year_str), data=MyData) + 
  geom_histogram()

ggplot(aes(x=income, group=year_str, fill=year_str), data=MyData) + 
  geom_histogram()

ggplot(aes(x=income, y=total_ghg, colour=RGN11NM), data=MyData) + #, group=MSOA
  geom_smooth(method='lm') + ggtitle("Varying Slopes") + 
  facet_grid(. ~ year_str)

ggplot(aes(x=income, y=total_ghg, colour=q_ghg_str), data=MyData) + 
  geom_smooth(method='lm') + ggtitle("Varying Slopes") + 
  facet_grid(. ~ year_str)
#grid.arrange(p1, p2, p3, p4, nrow = 2)

# these charts suggest that:
# BMI change is approximated well as linear for males and quadratic for females 
# TVW change is approximated well as quadratic for females and linear for males

#######################################
## Multilevel Random Intercept Model ##
#######################################

# we encode males and females separately with binary indicators, centre Time & create Time^2
# and create new covariates to facilitate more complex parameterisation
MyData$T1 <- MyData$year - (2007+2017)/2
MyData$income <- MyData$income / 10000
head(MyData)

# we explore a multilevel random intercept model for BMI with the suggested parameterisation
mod1 <- lmer(total_ghg ~ T1 + income + (1|MSOA), data=MyData)
summary(mod1)

# mean BMI for females is 10.13, slope for females is 1.27
# mean BMI for males is lower by -0.70 at 9.43, slope for males is less by -0.53 at 0.74
# mean quadratic 'acceleration' for females is -0.05, so a slight deceleration
# but is this a better fitting model than assuming just linear change in BMI for both sexes?
mod2 <- lmer(total_ghg ~ T1 * income + (1|MSOA), data=MyData)
summary(mod2); BIC(mod1); BIC(mod2)

# the BIC suggests there is little merit in the quadratic term for females
# the preferred model is bmi2

# we now run a multilevel random effects model for the BMI data
# we allow slopes for males and females to vary jointly - this follows a Normal distribution 
mod2 <- lmer(total_ghg ~ T1 + income + (1+T1|MSOA), data=MyData)
summary(mod2); BIC(mod1); BIC(mod2)


mod2 <- lmer(total_ghg ~ T1 + income + (T1|MSOA), data=MyData)
summary(mod2); BIC(mod1); BIC(mod2)


corr(MyData$total_ghg, MyData$income)
mod3 <- lm(total_ghg ~ income, data = MyData) 
summary(mod3); BIC(mod3)


# the random slope model is a superior fit according to BIC (4953.6)
# the variance of the random slope is 0.15 
# Note: the parameterisation adopted does not allow for random slopes to vary to a  
# different degree for males and females - it is currently assumed that their variation
# is homogeneous (notwithstanding that their means are different)

# we repeat for the longitudinal outcome measure TVW and explore cubic parameterisations

#######################################
## Multilevel Random Intercept Model ##
#######################################

# we encode males and females separately with binary indicators, centre Time & create Time^2
# and create new covariates to facilitate more complex parameterisation
TVW$Male   <- as.integer(TVW$Sex=="Male")
TVW$Female <- as.integer(TVW$Sex=="Female")
TVW$cSex   <- TVW$Male - 0.5 
TVW$T1     <- TVW$Time - 2.5
TVW$T2     <- TVW$T1 * TVW$T1
TVW$T2_F   <- TVW$T2 * TVW$Female 
head(TVW)

# we explore a multilevel random intercept model for TVW with the suggested parameterisation
tvw1 <- lmer(TVW ~ T1*cSex + T2_F + (1|Id), data=TVW)
summary(tvw1)

# mean TVW for females is 10.13, slope for females is 1.27
# mean TVW for males is lower by -0.70 at 9.43, slope for males is less by -0.53 at 0.74
# mean quadratic 'acceleration' for females is -0.05, so a slight deceleration
# but is this a better fitting model than assuming just linear change in TVW for both sexes?
tvw2 <- lmer(TVW ~ T1*cSex + (1|Id), data=TVW)
summary(tvw2)
BIC(tvw1); BIC(tvw2)
AIC(tvw1); AIC(tvw2)

# the BIC suggests there is little merit in the quadratic term for females
# the preferred model is tvw2

# we now run a multilevel random effects model for the TVW data
# we allow slopes for males and females to vary jointly - this follows a Normal distribution 
tvw3 <- lmer(TVW ~ T1*cSex + (1 + T1 | Id), data=TVW)
summary(tvw3)
BIC(tvw2); BIC(tvw3)

# the random slope model is a superior fit according to BIC (4953.6)
# the variance of the random slope is 0.15 
# Note: the parameterisation adopted does not allow for random slopes to vary to a  
# different degree for males and females - it is currently assumed that their variation
# is homogeneous (notwithstanding that their means are different)

TVW$cSex   <- TVW$Male - 0.5 
TVW$T1_M   <- TVW$T1 * TVW$Male
TVW$T1_F   <- TVW$T1 * TVW$Female 
head(TVW)

tvw4 <- lmer(TVW ~ T1_M*cSex + T1_F*cSex + (1 + T1 | Id), data=TVW)
summary(tvw4)
BIC(tvw3); BIC(tvw4)

tvw5 <- lmer(TVW ~ T1_M*cSex + T1_F*cSex + (1 + T1_M + T1_F | Id), data=TVW)
summary(tvw5)
BIC(tvw4); BIC(tvw5)

# we repeat for the longitudinal outcome measure TVW and explore cubic parameterisations