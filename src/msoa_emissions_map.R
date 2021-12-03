# Required libraries.
library(tidyverse)
library(sf)
library(nlme) 
library(GWmodel) 
library(tmap) 
library(lsr)
library(broom)
library(maps)

setwd("~/Documents/Ausbildung/UoLeeds/PhD/Analysis")

# new with wide format
shp_data <- read_sf(paste('data/processed/GWR_data/gwr_data_london_2015.shp', sep='')) %>%
  st_transform(CRS("+proj=tmerc +lat_0=49 +lon_0=-2 +k=0.9996012717 +x_0=400000 +y_0=-100000 +ellps=airy +units=m +no_defs")) 

product_list <- shp_data %>% st_drop_geometry %>% select(income:bame, -income, -bame) %>% names()

for (product in product_list){
  midpoint <- shp_data %>% st_drop_geometry %>% select(product) %>% apply(2, median)
  map <- tm_shape(shp_data) +
    tm_fill(product, mid="#ffffff", midpoint=midpoint, style = "quantile", n=5, title=expression("tCO"[2]*"e/capita"),
            palette = "-RdBu") + 
    tm_borders(lwd = 0.1) +
    tm_layout(frame = F, title=paste(product), title.position = c(0, 0.999), title.size = 0.5,
              legend.position = c(0.8, 0), legend.title.size = 2, legend.title.fontfamily="Times New Roman", 
              legend.text.size = 1.5, legend.text.fontfamily="Times New Roman", outer.margins=c(0, 0, 0, 0.11))
  tmap_save(map, paste('Spatial_Emissions/outputs/Maps/London_', str_replace_all(product, "[^[:alnum:]]", ""), '.png', sep=''))
}

#  scale_fill_steps2(high="#B7736B", mid="#ffffff", low="#746BB4", midpoint=midpoint, name=) +
# for (product in product_list){
#   midpoint <- shp_data %>% st_drop_geometry %>% select(product) %>% apply(2, median)
#   map <- ggplot() +
#     geom_sf(data=shp_data, aes(fill=product), color = "#3d3d3d", size=0.05) + 
#     scale_fill_steps2(high="#B7736B", mid="#ffffff", low="#746BB4", midpoint=midpoint, name=expression(atop("London Median", "(tCO"[2]*"e/capita)"))) + #  high="#A48AAE", mid="#94C9C7", low="#FAF39A",
#     theme(legend.position = c(0.875, 0.22), legend.text = element_text(colour="black", size=15, family="Times New Roman"), legend.title = element_text(colour="black", size=15, family="Times New Roman"))
#   tmap_save(map, paste('Spatial_Emissions/outputs/Maps/London_', str_replace_all(product, "[^[:alnum:]]", ""), '.png', sep=''))
#   }
