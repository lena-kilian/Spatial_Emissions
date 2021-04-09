# -------------------------------------------
# R script demonstrating how Covid-19 glyphmaps can be generated
# and parameterised
# Author: Roger Beecham
# -------------------------------------------

# -------------------------------------------
# L I B R A R I E S
# -------------------------------------------

# Required libraries.
library(tidyverse)
library(sf)
library(lubridate)
library(RcppRoll)
library(gganimate)

# Set theme.
theme_set(theme_minimal(base_family="Avenir Book"))
# Paired back theme.
theme_spare <- theme(axis.title=element_blank(),axis.text = element_blank(),panel.grid = element_blank())

# -------------------------------------------
# F U N C T I O N
# -------------------------------------------

# Plot function
generate_line <- function(data, cell_size) {
  plot <- data %>% 
    ggplot()+
    geom_sf(data=. %>% select(area_nm, fill) %>% unique, aes(fill=fill), color = "#636363", size=0.01)+ 
    geom_sf(data=filter(regions, regn_nm == 'London') , fill = NA, color = "#636363", size=0.5) + 
    coord_sf(crs=27700, datum=NA, clip="off")+
    geom_point(data=data, aes(x=easting+x-cell_size, y=northng+y-cell_size), pch=21, size=0.001, fill="#636363", colour="#636363", alpha=.7)+
    # Case data.
    geom_path(
      aes(x=easting+x-cell_size, y=northng+y-cell_size, group=area_nm, colour=colour, size=size), 
      lineend="round" 
    )
  return(plot)
}


# Total function
run_plot <- function(my_data, variable, cell_height, grid_data) {
  # rescale
  data <- my_data
  data['rescaled'] <- data[variable]
  data <- mutate(data, rescaled=scales::rescale(rescaled, to=c(0, cell_height), from = c(min(rescaled), max(rescaled))))

  # get means
  mean <- select(my_data, area_nm, variable, population)
  mean['year_mean'] = mean[variable] * mean$population
  uk_mean = sum(mean$year_mean) / sum(mean$population)
  mean <- mean %>%
    group_by(area_nm) %>%
    summarise_at(vars(year_mean, population), list(sum)) %>%
    ungroup() %>%
    mutate(year_mean = year_mean / population)
  data <- left_join(data, (select(mean, year_mean, area_nm)), by='area_nm')
  
  # plot
  plot_data <- grid_data %>% inner_join(data, by='area_nm') %>%  ungroup %>% 
    mutate(x=years_rescaled, y=rescaled, colour=as.character(1), 
           size=0.1, fill=year_mean, alpha=1)
  
  lines <- generate_line(data=plot_data, cell_size=cell_height*.5) +
    scale_size(range=c(0,1), limits=c(0,1), guide=FALSE)+
    scale_colour_manual(values=c("#636363"), guide=FALSE) +
    scale_fill_steps2(high="#B7736B", mid="white", low="#746BB4", midpoint=uk_mean, name=paste('2007-2017 Mean')) + 
    #scale_fill_continuous(type = "viridis") +
    #scale_fill_manual(values=c("#d9d9d9", "#bdbdbd"), guide=FALSE) +
    scale_alpha(range=c(1,1), guide=FALSE) +
    # Uncomment line below when animating.
    # transition_reveal(date) +
    theme_spare
  
  return(lines)
}


# -------------------------------------------
# D A T A
# -------------------------------------------
grids <- read_sf("data/processed/Geography/lad_grid.shp")
ghg_data <- read_csv("data/processed/ghg_income_uaa_lad_grid.csv")
regions <- grids %>% group_by(regn_nm) %>% summarise() %>% ungroup()

# rescale variables
cell_height <- grids %>% st_drop_geometry() %>% 
  filter(case_when(x==9 & y==10 ~ TRUE,
                   x==10 & y==10 ~ TRUE,
                   TRUE ~ FALSE)) %>% 
  transmute(diff=easting-lag(easting,1)) %>% filter(!is.na(diff), diff>0) %>% pull

ghg_data <- mutate(ghg_data, years_rescaled=scales::rescale(year, to=c(0, cell_height), from = c(2007, 2017)))

# -------------------------------------------
# P L O T S
# -------------------------------------------

# These examples depend on data being downloaded (download_data.R), staged  
# (data_staging.R) and also the associated  helper functions (helper_functions.R). 
# So if you have not already, run those now by uncommenting the lines below.
# source("./code/download_data.R")
# source("./code/data_staging.R")
# source("./code/helper_functions.R")


# T H I C K N E S S 

# Mappings 
# size (mark thickness) : relative cases counts
# colour (mark colour) : not encoded 
# alpha (mark lightness) : not encoded 

for (var in c('1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', 'total_ghg', 'Income anonymised')){
  lines <- run_plot(my_data=ghg_data, variable=var, cell_height=cell_height, grid_data=grids)
  ggsave(paste('outputs/Glyphmaps/glyphmaps_', var, '.png', sep=''))
}



