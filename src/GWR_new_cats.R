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

shp_data <- read_sf("data/processed/new_cat_for_gwr.shp") %>% 
  mutate(income = Income.ano/100)

london <- filter(shp_data, RGN11NM == 'London')

# -------------------------------------------
# 2017 by products
# -------------------------------------------

for (yr in c(2007, 2009, 2011, 2013, 2015)){
  year_data = london %>% filter(year == yr)
  for (product in c("food..anim", "clothing", "home.energ", "private.tr", "public.tra", "air.transp", "total_ghg")){
    temp <- year_data %>% rename(ghg=product)
    # convert to sp
    mydata.sp <- as(temp, "Spatial")
    # determine the kernel bandwidth & fit GWR
    bw <- bw.gwr(ghg ~ income, adaptive = T, data=mydata.sp)
    m.gwr <- gwr.basic(ghg ~ income, adaptive = T, data = mydata.sp, bw = bw)
    gwr_sf <- st_as_sf(m.gwr$SDF) 
    
    # save local coef
    msoa_yr <- data_frame(temp$index) %>%
      mutate(MSOA11CD = `temp$index`)
    msoa_yr[paste('LC', yr, product, sep='_')] <- data_frame(gwr_sf)$income
    write.csv(msoa_yr, paste('Spatial_Emissions/outputs/GWR/local_coef_london_', yr, '_', str_replace_all(product, "[^[:alnum:]]", ""), '.csv', sep=''))
    
    # map local coef
    map <- tm_shape(gwr_sf) +
      tm_fill('income', midpoint = 0) + #, style = "kmeans") + 
      tm_style("col_blind") +
      tm_layout(legend.position = c("right","top"), frame = F)
    tmap_save(map, paste('Spatial_Emissions/outputs/GWR/London_', yr, '_', str_replace_all(product, "[^[:alnum:]]", ""), '.png', sep=''))
    
    tab <- rbind(apply(m.gwr$SDF@data[, 1:2], 2, summary), coef(m.gwr$lm)) 
    rownames(tab)[7] <- "Global"
    tab <- round(tab, 3)
    
    write.csv(t(tab), file = paste('Spatial_Emissions/outputs/GWR/global_coef_london_', yr, '_', str_replace_all(product, "[^[:alnum:]]", ""), '.csv', sep=''))
  }
}

