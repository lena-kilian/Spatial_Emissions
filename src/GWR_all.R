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
# -------------------------------------------
# D A T A
# -------------------------------------------
yr <- 2015

shp_data <- read_sf(paste('data/processed/GWR_data/gwr_data_london_', yr, '.shp', sep='')) %>%
  mutate(total_inc = income * population / 1000, 
         total_work = avg_workpl * population / 10,
         MSOA11CD = index)

# -------------------------------------------
# 2017 by products
# -------------------------------------------
product_list = c("Car.van.pu", "Rail.and.b", "Flights")

# Only control for population
for (product in product_list){ #'rental_tax', 'water',  'other_priv'
  for (variable in c('total_work', 'AI2015_ln', 'lim', 'pop_65.', 'pop_14.', 'total_inc', 'bame')){
    temp <- shp_data %>% rename(ghg=product, predictor=variable) %>% select(MSOA11CD, predictor, ghg, geometry, population) %>% drop_na() %>% st_as_sf()
    # convert to sp
    mydata.sp <- as(temp, "Spatial")
    # determine the kernel bandwidth & fit GWR
    bw <- bw.gwr(ghg ~ predictor + population, adaptive = 30, data=mydata.sp)
    m.gwr <- gwr.basic(ghg ~ predictor + population, adaptive = T, data = mydata.sp, bw = bw)
    gwr_sf <- st_as_sf(m.gwr$SDF) 
    
    # plot residuals
    par(mfrow=c(2,2))
    m.lm <- lm(ghg ~ predictor + population, data=st_drop_geometry(temp))
    res <- m.gwr$SDF$residual
    plot(x=m.gwr$SDF$yhat, y=res)
    qqnorm(res)
    plot(x=hatvalues(m.lm), y=res)
    plot(density(res))
    dev.copy(png, paste('Spatial_Emissions/outputs/GWR/residuals_plots/Residual_plots_', str_replace_all(product, "[^[:alnum:]]", ""), '_', 
                        str_replace_all(variable, "[^[:alnum:]]", ""), '_',  yr, '.png', sep=''))
    dev.off()
    
    # save local coef
    msoa_yr <- temp %>% as_tibble() %>% select(MSOA11CD)
    msoa_yr[paste('LC', yr, product, sep='_')] <- data_frame(gwr_sf)$predictor
    write.csv(msoa_yr, paste('Spatial_Emissions/outputs/GWR/local_coeffs/local_coef_london_', str_replace_all(product, "[^[:alnum:]]", ""), 
                             '_', str_replace_all(variable, "[^[:alnum:]]", ""), '_',  yr, '.csv', sep=''))
    
    # map local coef
    map <- tm_shape(gwr_sf) +
      tm_fill('predictor', midpoint = 0, style = "kmeans", title="Local Coefficients") + 
      tm_style("col_blind") +
      tm_borders(lwd = 0.1) +
      tm_layout(frame = F, title=paste(product, variable, 'w_inc', sep='_'), title.position = c(0, 0.999), title.size = 0.5,
                legend.position = c(0.8, 0.1), legend.title.size = 1.3, legend.title.fontfamily="Times New Roman", 
                legend.text.size = 1, legend.text.fontfamily="Times New Roman")
    tmap_save(map, paste('Spatial_Emissions/outputs/GWR/maps/London_', str_replace_all(product, "[^[:alnum:]]", ""), 
                         '_', str_replace_all(variable, "[^[:alnum:]]", ""), '_',  yr, '.png', sep=''))
    # make global summary
    temp <- summary(m.gwr$lm)$coef %>% t()
    rownames(temp)[1] <- "Global Estimate"
    rownames(temp)[2] <- "Global St. Er."
    rownames(temp)[3] <- "Global tval"
    rownames(temp)[4] <- "Global pval"
    
    tab <- rbind(apply(m.gwr$SDF@data[, 1:3], 2, summary), temp) 
    
    temp2 <- data.frame(m.gwr$GW.diagnostic %>% as_tibble())
    rownames(temp2) <- c("Global")
    
    tab <- tab %>% cbind(temp2) %>% round(3)
    colnames(tab)[2] <- variable
    
    write.csv(tab, file = paste('Spatial_Emissions/outputs/GWR/global_coeffs/global_coef_london_', str_replace_all(product, "[^[:alnum:]]", ""), 
                                   '_', str_replace_all(variable, "[^[:alnum:]]", ""), '_',  yr, '.csv', sep=''))
  }
}

# Also control for income
for (product in product_list){ #'rental_tax', 'water',  'other_priv'
  for (variable in  c('total_work', 'AI2015_ln', 'lim', 'pop_65.', 'pop_14.', 'total_inc', 'bame')){
    temp <- shp_data %>% rename(ghg=product, predictor=variable) %>% select(MSOA11CD, predictor, ghg, geometry, population, total_inc) %>% 
      drop_na() %>% st_as_sf()
    # convert to sp
    mydata.sp <- as(temp, "Spatial")
    # determine the kernel bandwidth & fit GWR
    bw <- bw.gwr(ghg ~ predictor + population + total_inc, adaptive = 30, data=mydata.sp)
    m.gwr <- gwr.basic(ghg ~ predictor + population + total_inc, adaptive = T, data = mydata.sp, bw = bw)
    gwr_sf <- st_as_sf(m.gwr$SDF)
    
    # plot residuals
    par(mfrow=c(2,2))
    m.lm <- lm(ghg ~ predictor + population + total_inc, data=st_drop_geometry(temp))
    res <- m.gwr$SDF$residual
    plot(x=m.gwr$SDF$yhat, y=res)
    qqnorm(res)
    plot(x=hatvalues(m.lm), y=res)
    plot(density(res))
    dev.copy(png, paste('Spatial_Emissions/outputs/GWR/residuals_plots/Residual_plots_', str_replace_all(product, "[^[:alnum:]]", ""), '_', 
                        str_replace_all(variable, "[^[:alnum:]]", ""), '_',  yr, '_w-inc.png', sep=''))
    dev.off()
    
    # save local coef
    msoa_yr <- temp %>% as_tibble() %>% select(MSOA11CD)
    msoa_yr[paste('LC', yr, product, sep='_')] <- data_frame(gwr_sf)$predictor
    write.csv(msoa_yr, paste('Spatial_Emissions/outputs/GWR/local_coeffs/local_coef_london_', str_replace_all(product, "[^[:alnum:]]", ""), 
                             '_', str_replace_all(variable, "[^[:alnum:]]", ""), '_',  yr, '_w-inc.csv', sep=''))
    
    # map local coef
    map <- tm_shape(gwr_sf) +
      tm_fill('predictor', midpoint = 0, style = "kmeans", title="Local Coefficients") + 
      tm_style("col_blind") +
      tm_borders(lwd = 0.1) +
      tm_layout(frame = F, title=paste(product, variable, 'w_inc', sep='_'), title.position = c(0, 0.999), title.size = 0.5,
                legend.position = c(0.8, 0.1), legend.title.size = 1.3, legend.title.fontfamily="Times New Roman",
                legend.text.size = 1, legend.text.fontfamily="Times New Roman")
    tmap_save(map, paste('Spatial_Emissions/outputs/GWR/maps/London_', str_replace_all(product, "[^[:alnum:]]", ""), 
                         '_', str_replace_all(variable, "[^[:alnum:]]", ""), '_',  yr, '_w-inc.png', sep='')) 
    
    map <- tm_shape(gwr_sf) +
      tm_fill('total_inc', midpoint = 0, style = "kmeans", title="Local Coefficients") + 
      tm_style("col_blind") +
      tm_borders(lwd = 0.1) +
      tm_layout(frame = F, title=paste(product, variable, 'w_inc', sep='_'), title.position = c(0, 0.999), title.size = 0.5,
                legend.position = c(0.8, 0.1), legend.title.size = 1.3, legend.title.fontfamily="Times New Roman",
                legend.text.size = 1, legend.text.fontfamily="Times New Roman")
    tmap_save(map, paste('Spatial_Emissions/outputs/GWR/maps/INCOME_London_', str_replace_all(product, "[^[:alnum:]]", ""), 
                         '_', str_replace_all(variable, "[^[:alnum:]]", ""), '_',  yr, '_w-inc.png', sep='')) 
    
    
    # make global summary
    temp <- summary(m.gwr$lm)$coef %>% t()
    rownames(temp)[1] <- "Global Estimate"
    rownames(temp)[2] <- "Global St. Er."
    rownames(temp)[3] <- "Global tval"
    rownames(temp)[4] <- "Global pval"
    
    tab <- rbind(apply(m.gwr$SDF@data[, 1:4], 2, summary), temp) 

    temp2 <- data.frame(m.gwr$GW.diagnostic %>% as_tibble())
    rownames(temp2) <- c("Global")
    
    tab <- tab %>% cbind(temp2) %>% round(3) 
    colnames(tab)[2] <- variable
    
    write.csv(tab, file = paste('Spatial_Emissions/outputs/GWR/global_coeffs/global_coef_london_', str_replace_all(product, "[^[:alnum:]]", ""), 
                                   '_', str_replace_all(variable, "[^[:alnum:]]", ""), '_',  yr, '_w-inc.csv', sep=''))
  }
}



