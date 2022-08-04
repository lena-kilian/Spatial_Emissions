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
         total_work = avg_workpl * population / 10)

names(shp_data) <- c("MSOA11CD", "RGN11NM", "AI2015", "PTAL2015", "AI", "other", 
                     "Car", "Other", "Rail", "Bus", "Cf", "Flights", 
                     "population",
                     "pop_65._pc", "p65", "pop_14._pc", "p14", "not_lim", "not_lim_pc", "bame_pct", "work", "avg_workpl", "income",
                     "pc_Car.van", "pc_Other.t", "pc_Rail", "pc_Bus", "pc_Combine", "pc_Flights",
                     "bame", "lim", "geometry", "inc")

result_data <- select(shp_data, MSOA11CD)
  
shp_data <- st_drop_geometry(shp_data)

# -------------------------------------------
# 2017 by products
# -------------------------------------------
product_list <- shp_data %>% select(other:population, -other, -population) %>% names()

#provide column names
colnames(df) <- c('var1', 'var2', 'var3')
# get R2 for all models
for (product in product_list){ #'rental_tax', 'water',  'other_priv'
  for (variable in c('work', 'AI', 'lim', 'p65', 'p14', 'inc', 'bame')){
    # create for loops to run income and others in same run
    if (variable == 'inc'){
      temp <- shp_data %>% rename(ghg=product, predictor=variable) %>% select(MSOA11CD, predictor, ghg, population) %>% drop_na()
      formula <-'ghg ~ predictor + population'}
    if (variable != 'inc'){
      temp <- shp_data %>% rename(ghg=product, predictor=variable) %>% select(MSOA11CD, predictor, ghg, population, inc) %>% drop_na()
      formula <-'ghg ~ predictor + population + inc'}
    
    # run linear regression model for all
    mod <- lm(formula, data = temp)
    
    # save results 
    result_data[paste(product, variable, sep='_')] <- mod$residuals
    }
}

st_write(result_data, "data/processed/GWR_data/LM_residuals.shp", append=FALSE) 

