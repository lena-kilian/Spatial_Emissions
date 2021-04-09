# Required libraries.
library(tidyverse)
library(sf)
library(nlme) 
library(GWmodel) 
library(tmap) 

setwd("~/Documents/Ausbildung/UoLeeds/PhD/Analysis/Spatial_Emissions")
# -------------------------------------------
# D A T A
# -------------------------------------------

shp_data <- read_sf("data/raw/Geography/Shapefiles/UK/msoa_2011_uk_all.shp")
ghg_data <- read_csv("data/processed/modelling_data.csv")

#shp_data <- read_sf("data/processed/Geography/lad_grid.shp")
#ghg_data <- read_csv("data/processed/ghg_income_uaa_lad_grid.csv")

# -------------------------------------------
# 2017 Regions
# -------------------------------------------

mydata <- shp_data %>%
  mutate(MSOA = MSOA11CD) %>%
  inner_join(filter(ghg_data, year == 2017), by='MSOA') %>%
  mutate(income = income / 10000)
  #inner_join(filter(ghg_data, year == 2017), by='area_nm') %>%
  #mutate(income = `Income anonymised` / 10000)

regions = c('London', 'North West', 'Yorkshire and The Humber', 'North East', 
            'West Midlands', 'East Midlands', 'South West', 'East of England', 'South East')
for (region in regions){
  # convert to sp
  mydata.sp = as(filter(mydata, RGN11NM == region), "Spatial")
  # determine the kernel bandwidth
  bw <- bw.gwr(total_ghg ~ income, adaptive = T, data=mydata.sp)
  bw
  
  m.gwr <- gwr.basic(total_ghg ~ income, adaptive = T, data = mydata.sp, bw = bw)
  m.gwr
  
  gwr_sf = st_as_sf(m.gwr$SDF) 
  gwr_sf
  
  
  map <- tm_shape(gwr_sf) +
    tm_fill('income', midpoint = 0) + #, style = "kmeans") + 
    tm_style("col_blind") +
    tm_layout(legend.position = c("right","top"), frame = F)
  tmap_save(map, paste('outputs/GWR/', region, '.png', sep=''))
  
  tab <- rbind(apply(m.gwr$SDF@data[, 1:2], 2, summary), coef(m.gwr$lm)) 
  rownames(tab)[7] <- "Global"
  tab <- round(tab, 3)
  
  write.csv(t(tab), file = paste('outputs/GWR/coef_', region, '.csv', sep=''))
  
  # determine significance
  # determine which are significant
  
  #tval = gwr_sf$income
  #signif = tval < -1.96 | tval > 1.96 # map the counties
  #tm_shape(gwr_sf) +
   # tm_fill("income", midpoint = 0) + 
   # tm_style("col_blind")+ 
  #  tm_layout(legend.position = c("right","top")) +
    # now add the tvalues layer
  #  tm_shape(gwr_sf[signif,]) + 
   # tm_borders()
}
  
# -------------------------------------------
# UK by years
# -------------------------------------------

mydata <- shp_data %>%
  mutate(MSOA = MSOA11CD) %>%
  inner_join(ghg_data, by='MSOA') %>%
  mutate(income = income / 10000)
#inner_join(filter(ghg_data, year == 2017), by='area_nm') %>%
#mutate(income = `Income anonymised` / 10000)

years = c(2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017)
local_coef <- mydata %>% filter(year == 2017) %>% select('MSOA')
for (yr in years){
  # convert to sp
  temp <- mydata %>% filter(year_str == paste('Y', yr, sep=''))
  mydata.sp <- as(temp, "Spatial")
  # determine the kernel bandwidth & fit GWR
  bw <- bw.gwr(total_ghg ~ income, adaptive = T, data=mydata.sp)
  m.gwr <- gwr.basic(total_ghg ~ income, adaptive = T, data = mydata.sp, bw = bw)
  gwr_sf <- st_as_sf(m.gwr$SDF) 
  
  # save local coef
  msoa_yr <- data_frame(temp$MSOA) %>%
    mutate(MSOA = `temp$MSOA`)
  msoa_yr[paste('Y', yr, sep='')] <- data_frame(gwr_sf)$income
  
  local_coef <- left_join(local_coef, select(msoa_yr, -`temp$MSOA`), by='MSOA')
  
  # map local coef
  map <- tm_shape(gwr_sf) +
    tm_fill('income', midpoint = 0) + #, style = "kmeans") + 
    tm_style("col_blind") +
    tm_layout(legend.position = c("right","top"), frame = F)
  tmap_save(map, paste('outputs/GWR/UK_', yr, '.png', sep=''))
  
  tab <- rbind(apply(m.gwr$SDF@data[, 1:2], 2, summary), coef(m.gwr$lm)) 
  rownames(tab)[7] <- "Global"
  tab <- round(tab, 3)
  
  write.csv(t(tab), file = paste('outputs/GWR/coef_', yr, '.csv', sep=''))
}


# Save local coefs
st_write(local_coef, 'outputs/local_coefficients_2007-17.shp')
