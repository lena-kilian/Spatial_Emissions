# Required libraries.
library(tidyverse)
library(sf)
library(nlme) 
library(GWmodel) 
library(tmap) 
library(lsr)

setwd('~/Documents/Ausbildung/UoLeeds/PhD/Analysis/')
# -------------------------------------------
# D A T A
# -------------------------------------------

shp_data <- read_sf('data/processed/GWR_data/transport_access.shp')

census_data <- read_csv('data/processed/GWR_data/census_variables.csv')

# -------------------------------------------
# 2017 by products
# -------------------------------------------
yr <- 2017

for (product in c('Petrol', 'other_priv', 'rail_bus', 'air', 'rental_tax', 'water')){
    temp <- shp_data %>% rename(ghg=product) %>% select(MSOA11CD, AI2015_ln, ghg, geometry, pop) %>% drop_na() %>% st_as_sf()
    # convert to sp
    mydata.sp <- as(temp, "Spatial")
    # determine the kernel bandwidth & fit GWR
    bw <- bw.gwr(ghg ~ AI2015_ln + pop, adaptive = 30, data=mydata.sp)
    m.gwr <- gwr.basic(ghg ~ AI2015_ln + pop, adaptive = T, data = mydata.sp, bw = bw)
    gwr_sf <- st_as_sf(m.gwr$SDF) 
    
    # save local coef
    msoa_yr <- temp %>% as_tibble() %>% select(MSOA11CD)
    msoa_yr[paste('LC', yr, product, sep='_')] <- data_frame(gwr_sf)$AI2015_ln
    write.csv(msoa_yr, paste('Spatial_Emissions/outputs/GWR/transport_access_local_coef_london_', str_replace_all(product, "[^[:alnum:]]", ""), '_', yr, '.csv', sep=''))
    
    # map local coef
    map <- tm_shape(gwr_sf) +
      tm_fill('AI2015_ln', midpoint = 0) + #, style = "kmeans") + 
      tm_style("col_blind") +
      tm_layout(legend.position = c("right","top"), frame = F)
    tmap_save(map, paste('Spatial_Emissions/outputs/GWR/transport_access_London_', str_replace_all(product, "[^[:alnum:]]", ""), '_', yr, '.png', sep=''))
    
    tab <- rbind(apply(m.gwr$SDF@data[, 1:2], 2, summary), coef(m.gwr$lm)) 
    rownames(tab)[7] <- "Global"
    tab <- round(tab, 3)
    
    write.csv(t(tab), file = paste('Spatial_Emissions/outputs/GWR/transport_access_global_coef_london_', str_replace_all(product, "[^[:alnum:]]", ""), '_', yr, '.csv', sep=''))
}



