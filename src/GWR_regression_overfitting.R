# Required libraries.
library(tidyverse)
library(sf)
library(nlme) 
library(GWmodel) 
library(tmap) 
library(lsr)
library(broom)
library(maps)

setwd('~/Documents/Ausbildung/UoLeeds/PhD/Analysis/')
set.seed(123)
# -------------------------------------------
# D A T A
# -------------------------------------------
yr <- 2015

n <- 5
style <- "kmeans"

shp_data <- read_sf(paste('data/processed/GWR_data/gwr_data_london_', yr, '.shp', sep='')) %>%
  st_transform(CRS("+proj=tmerc +lat_0=49 +lon_0=-2 +k=0.9996012717 +x_0=400000 +y_0=-100000 +ellps=airy +units=m +no_defs")) %>%
  mutate(total_inc = income * population / 1000, 
         total_work = avg_workpl * population / 10,
         MSOA11CD = index) %>%
  st_drop_geometry()

# -------------------------------------------
# 2017 by products
# -------------------------------------------
product_list <- shp_data %>% select(other:population, -other, -population) %>% names()


results <- data.frame(matrix(ncol = 2, nrow = 0))
colnames(results) <- c('product', 'predictor')

#provide column names
colnames(df) <- c('var1', 'var2', 'var3')
# get R2 for all models
for (product in product_list){ #'rental_tax', 'water',  'other_priv'
  for (variable in c('total_work', 'AI2015_ln', 'lim', 'pop_65.', 'pop_14.', 'total_inc', 'bame')){
    # create for loops to run income and others in same run
    if (variable == 'total_inc'){
      temp <- shp_data %>% rename(ghg=product, predictor=variable) %>% select(MSOA11CD, predictor, ghg, population) %>% drop_na()
      formula <-'ghg ~ predictor + population'}
    if (variable != 'total_inc'){
      temp <- shp_data %>% rename(ghg=product, predictor=variable) %>% select(MSOA11CD, predictor, ghg, population, total_inc) %>% drop_na()
      formula <-'ghg ~ predictor + population + total_inc'}
    
    # run linear regression model for all
    mod <- lm(formula, data = temp)
    
    # save results 
    results.temp <- data.frame(matrix(ncol = 0, nrow = 1))
    results.temp$prodcut <- product
    results.temp$predictor <- variable
    results.temp$formula <- formula
    results.temp$adjR2 <- summary(mod)$adj.r.squared
    
    # run cross validation
    temp.shuffle <- temp[sample(1:nrow(temp)), ]
    temp.shuffle$cv_group <- rep(seq(1, 10), ceiling(nrow(temp.shuffle)/10))[1:nrow(temp.shuffle)]
    
    for (i in seq(1, 10)){
      temp.train <- filter(temp.shuffle, cv_group != i)
      temp.test <- filter(temp.shuffle, cv_group == i)
      
      mod.train <- lm(formula, data = temp.train)
      temp.test$predicted_vals <- predict(mod.train, temp.test)
      
      mse <- mean((temp.test$ghg - temp.test$predicted_vals)**2)
      results.temp[paste('cv_', i, sep='')] <- sqrt(mse)}
    
    results <- rbind(results, results.temp)
    }
}



