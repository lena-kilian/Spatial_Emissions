# Required libraries.
library(tidyverse)
library(sf)
library(nlme) 
library(GWmodel) 
library(tmap) 
library(lsr)

setwd("~/Documents/Ausbildung/UoLeeds/PhD/Analysis/")
# -------------------------------------------
# D A T A
# -------------------------------------------

shp_data <- read_sf("data/raw/Geography/Shapefiles/UK/msoa_2011_uk_all.shp")
ghg_data <- read_csv("data/processed/GWR_model_product_data.csv") %>%
  mutate(MSOA11CD = X1, income = `Income anonymised`) %>%
  select(-X1, -`Income anonymised`) %>%
  gather('COICOP1', 'ghg', c(`1`:`12`))

#shp_data <- read_sf("data/processed/Geography/lad_grid.shp")
#ghg_data <- read_csv("data/processed/ghg_income_uaa_lad_grid.csv")
  
# -------------------------------------------
# 2017 by products
# -------------------------------------------

mydata <- shp_data %>%
  mutate(MSOA = MSOA11CD) %>%
  inner_join(ghg_data, by='MSOA11CD') %>%
  mutate(income = income / 100)

local_coef <- ghg_data %>% filter(year == 2017) %>% select('MSOA11CD')
for (product_code in c(9)){
  product = as.character(product_code)
  product_data = mydata %>% filter(COICOP1 == product)
  for (yr in c(2007:2017)){
    # convert to sp
    temp <- product_data %>% filter(year == yr)
    mydata.sp <- as(temp, "Spatial")
    # determine the kernel bandwidth & fit GWR
    bw <- bw.gwr(ghg ~ income, adaptive = T, data=mydata.sp)
    m.gwr <- gwr.basic(ghg ~ income, adaptive = T, data = mydata.sp, bw = bw)
    gwr_sf <- st_as_sf(m.gwr$SDF) 
    
    # save local coef
    msoa_yr <- data_frame(temp$MSOA) %>%
      mutate(MSOA11CD = `temp$MSOA`)
    msoa_yr[paste('LC', yr, product, sep='_')] <- data_frame(gwr_sf)$income
    
    local_coef <- left_join(local_coef, select(msoa_yr, -`temp$MSOA`), by='MSOA11CD')
    
    # map local coef
    map <- tm_shape(gwr_sf) +
      tm_fill('income', midpoint = 0) + #, style = "kmeans") + 
      tm_style("col_blind") +
      tm_layout(legend.position = c("right","top"), frame = F)
    tmap_save(map, paste('Spatial_Emissions/outputs/GWR/UK_ccp1_', yr, '_', product, '.png', sep=''))
    
    tab <- rbind(apply(m.gwr$SDF@data[, 1:2], 2, summary), coef(m.gwr$lm)) 
    rownames(tab)[7] <- "Global"
    tab <- round(tab, 3)
    
    write.csv(t(tab), file = paste('Spatial_Emissions/outputs/GWR/coef_ccp1_', yr, '_', product, '.csv', sep=''))
  }
}


# Save local coefs
st_write(local_coef, 'Spatial_Emissions/outputs/local_coefficients_products_1-4-7-9.shp')
