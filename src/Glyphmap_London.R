# Required libraries.
library(tidyverse)
library(sf)
library(nlme) 
library(GWmodel) 
library(tmap) 
library(lsr)
library(lubridate)
library(RcppRoll)
library(gganimate)
library(geogrid)
library(grDevices)

setwd("~/Documents/Ausbildung/UoLeeds/PhD/Analysis/")
# -------------------------------------------
# D A T A
# -------------------------------------------

shp_data <- read_sf("data/processed/GWR_data/london_grid_w_data_newcats.shp")

my_data <- shp_data %>% 
  mutate(easting = ifelse(minx < 530000 & width < 3000, maxx - 3000, minx),
         northing = ifelse(miny < 180000 & width < 3000, maxy - 3000, miny),
         area_grid = (maxx-minx) * (maxy-miny),
         area_nm_str = paste('id', id, sep=''), area_nm = id) %>%
  arrange(year) 

#2007, 2009, 2011, 2013, 2015, 2017, 

products <- my_data %>% st_drop_geometry() %>% select(c(width:population)) %>% select(-width, -population) %>% names()

# Set theme.
theme_set(theme_minimal(base_family="Avenir Book"))
# Paired back theme.
theme_spare <- theme(axis.title=element_blank(),axis.text = element_blank(),panel.grid = element_blank())

#windowsFonts(A = windowsFont("Times New Roman"))

# -------------------------------------------
# F U N C T I O N
# -------------------------------------------

# Plot function
generate_line <- function(line_data, background_data, midpoint, margin) {
  temp <- ggplot() +
    geom_sf(data=background_data, aes(fill=year_mean), color = "#3d3d3d", size=0.05) + 
    coord_sf(crs=27700, datum=NA, clip="off")+
    scale_fill_steps2(high="#B7736B", mid="#ffffff", low="#746BB4", midpoint=midpoint, name=expression(atop("Mean", "tCO"[2]*"e/capita"))) + #  high="#A48AAE", mid="#94C9C7", low="#FAF39A",
    theme(legend.position = c(0.875, 0.22), legend.text = element_text(colour="black", size=15, family="Times New Roman"), legend.title = element_text(colour="black", size=15, family="Times New Roman"))
  plot <- temp +
    geom_point(data=line_data, aes(x=easting+x+margin, y=northing+y+margin), pch=21, alpha=0)+
    geom_path(data=line_data, aes(x=easting+x+margin, y=northing+y+margin, group=area_nm_str, size=0.2), color="black", lineend="round") +
    scale_size(range=c(0,1), limits=c(0,1), guide=FALSE)+
    scale_colour_manual(values=c("#636363"), guide=FALSE)
  return(plot)
}


# Total function
run_plot <- function(my_data, variable, margin) {
  # rescale
  cell_height <- 3000 - (margin*2)
  data <- my_data %>% st_drop_geometry() %>% distinct()
  data['my_var'] <- as.numeric(unlist(data[variable]))
  data <- data %>%
    mutate(y=scales::rescale(my_var, to=c(0, cell_height), from = c(min(my_var), max(my_var))),
           x=scales::rescale(year, to=c(0, cell_height), from = c(2007, 2017)))
  
  line_data <- data %>% #filter(width >= 2500 & height >= 2500)
    filter(area_grid >= 7200000)
  
  # get means
  mean <- data %>% select(area_nm, my_var, population) %>%
    mutate(year_mean = my_var * population) 
  london_mean <- sum(mean$year_mean) / sum(mean$population)
  mean <- mean %>%
    group_by(area_nm) %>%
    summarise_at(vars(year_mean, population), list(sum)) %>%
    ungroup() %>%
    mutate(year_mean = year_mean / population)
  background_data <- my_data %>% select(area_nm) %>% left_join(mean, by=c('area_nm'))
  
  lines <- generate_line(line_data=line_data, background_data=background_data, midpoint=london_mean, margin=margin) +
    scale_alpha(range=c(1,1), guide=FALSE) +
    theme_spare
  
  return(lines)
}


# -------------------------------------------
# P L O T S
# -------------------------------------------

for (var in products){
  lines <- run_plot(my_data=my_data, variable=var, margin=300) +
    labs(title = var)
  ggsave(paste('Spatial_Emissions/outputs/Glyphmaps/London_glyphmaps_', var, '.png', sep=''))
}

