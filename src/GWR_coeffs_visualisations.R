library(ggridges)
library(tidyverse)
library(purrr)

setwd("~/Documents/Ausbildung/UoLeeds/PhD/Analysis")

# # regression plot
# all_data <- read_csv('Spatial_Emissions/outputs/GWR/local_coeffs/all_for_plot.csv') %>%
#   mutate(var = paste(transport, pred, income_controlled, sep='_'),
#          group = as.integer(factor(var)),
#          income_controlled = ifelse(pred=='totalinc', TRUE, income_controlled)) %>%
#   #mutate(local_coeffs = ifelse(var == 'Flights_totalwork_FALSE', NA, local_coeffs),
#   ##       local_coeffs = ifelse(var == 'Flights_totalwork_TRUE', NA, local_coeffs),
#   #       local_coeffs = ifelse(var == 'Flights_AI2015ln_FALSE', NA, local_coeffs),
#   #       local_coeffs = ifelse(var == 'Flights_AI2015ln_True', NA, local_coeffs)) %>%
#   filter(var != 'Flights_totalwork_FALSE' & 
#            var != 'Flights_totalwork_TRUE' &
#            var != 'Flights_AI2015ln_FALSE' &
#            var != 'Flights_AI2015ln_TRUE') %>%
#   mutate(inc = ifelse(income_controlled == TRUE, 'Income controlled', 'Income not controlled'),
#          label_3 = ifelse(income_controlled == TRUE, 'y', 'n'))
# 
# order <- all_data %>% 
#   select(pred) %>% 
#   distinct() %>%
#   mutate(order = seq(7, 1),
#          order = ifelse(pred == 'totalinc', 8, order)) %>%
#   cbind(data_frame('predictors' = c('Public Transport Density', 'Pop. limited in day-to-day activities', 
#                                     'Pop. aged 65 or older', 'Pop. aged 14 or younger', 'Pop. identifying as BAME',
#                                     'Distance to workplace', 'Income'))) %>%
#   cbind(data_frame('label_2' = c('TD', 'LD', '65', '14', 'E', 'Dis', 'Inc')))
#   
# 
# my_cols <- all_data %>% 
#   select(transport) %>% 
#   distinct() %>% 
#   arrange(transport) %>% 
#   cbind(data_frame('colours' = c('#6D0021', '#C54A43', '#F1B593'))) %>% #'#9A576D'
#   cbind(data_frame('Transport Type' = c('Car/van purchases and motoring oils', 'Flights', 'Rail and bus'))) %>%
#   cbind(data_frame('label_1' = c('C', 'F', 'R')))
# 
# all_data <- all_data %>% left_join(order, by='pred') %>% left_join(my_cols, by='transport') %>% 
#   mutate(var = paste(order, pred, `Transport Type`, sep=' '),
#          label = paste(label_1, label_2, label_3, sep='-'))
# 
# text_data <- all_data %>% select(transport, pred, income_controlled, var, group, inc, predictors, label) %>% distinct() %>%
#   mutate(text_pos = -10.8)
# 
# y_labels <- all_data %>% select(var, predictors) %>% distinct() %>% arrange(var)
# ggplot() +
#   geom_density_ridges_gradient(data=all_data, aes(y=var, x=local_coeffs, fill=`Transport Type`)) +
#   scale_fill_manual(name = '', values = my_cols$colours) +
#   scale_y_discrete(name=' ', labels = y_labels$predictors, breaks=y_labels$var) +
#   guides(fill = guide_legend(override.aes = list(shape = 16))) +
#   geom_text(data=text_data, aes(y=var, vjust=-0.5, x=text_pos, label=label), colour="black", size=4, family="Times New Roman") + 
#   xlab('Local Coefficient') +
#   theme_classic() + 
#   facet_grid(. ~ inc) +
#   xlim(-13, 13) + 
#   geom_vline(xintercept=c(0,0), linetype="dotted") +
#   theme(legend.position = c('bottom'), text = element_text(colour="black", size=17, family="Times New Roman")) 
# 
# ggsave(paste('Spatial_Emissions/outputs/GWR/local_coeffs_plots/ridges_all.png', sep='_'))


# new with wide format
all_data <- read_csv('Spatial_Emissions/outputs/GWR/local_coeffs/all_for_plot.csv') %>%
  mutate(var = paste(transport, pred, income_controlled, sep='_'),
         group = as.integer(factor(var)),
         income_controlled = ifelse(pred=='totalinc', TRUE, income_controlled)) %>%
  filter(var != 'Flights_totalwork_FALSE' & 
           var != 'Flights_totalwork_TRUE' &
           var != 'Flights_AI2015ln_FALSE' &
           var != 'Flights_AI2015ln_TRUE') %>%
  mutate(inc = ifelse(income_controlled == TRUE, 'Income controlled', 'Income not controlled'),
         colours = ifelse(income_controlled == TRUE, '#C54A43', '#F1B593'),
         label_3 = ifelse(income_controlled == TRUE, 'y', 'n'))

my_cols <- all_data %>% 
  select(inc, colours) %>% 
  distinct() 

order <- all_data %>% 
  select(pred) %>% 
  distinct() %>%
  mutate(order = seq(7, 1),
         order = ifelse(pred == 'totalinc', 8, order)) %>%
  cbind(data_frame('predictors' = c('Public Transport Density', 'Pop. limited in day-to-day activities', 
                                    'Pop. aged 65 or older', 'Pop. aged 14 or younger', 'Pop. identifying as BAME',
                                    'Distance to workplace', 'Income'))) 
order$predictors_f = factor(order$predictors, levels=c('Distance to workplace', 
                                                       'Pop. identifying as BAME',
                                                       'Pop. aged 14 or younger',
                                                       'Pop. aged 65 or older',
                                                       'Pop. limited in day-to-day activities',
                                                       'Public Transport Density',
                                                       'Income'))

all_data <- all_data %>% left_join(order, by='pred') %>%
  mutate(var = paste(predictors, income_controlled, sep='_'))

order <- all_data %>% 
  select(var, predictors_f, income_controlled) %>% 
  distinct() %>%
  arrange(predictors_f, income_controlled)
order$var_f = factor(order$var, levels=c(order$var))

all_data <- all_data %>% left_join(select(order, var, var_f), by='var')

text_data <- all_data %>% select(transport, pred, income_controlled, var_f, group, inc, predictors, predictors_f) %>% distinct() %>%
  mutate(text_pos = -10.8) %>% arrange(var_f)

names <- all_data %>% 
  select(transport) %>% 
  distinct() %>% 
  arrange(transport) %>% 
  cbind(data_frame(transport_temp = c('Bus', 'Cars/vans', 'Combined fares', 'Flights', 'Rail')))

names$transport_f = factor(names$transport_temp, levels=c('Cars/vans', 'Flights', 'Rail', 'Bus', 'Combined fares'))

all_data <- all_data %>% left_join(names, by='transport') 

#y_labels <- all_data %>% select(var_f, pred, predictors, predictors_f) %>% distinct() %>% arrange(var_f)

# ggplot() +
#   geom_density_ridges_gradient(data=all_data, aes(y=var_f, x=local_coeffs, fill=inc)) +
#   scale_fill_manual(name = '', values = my_cols$colours) +
#   scale_y_discrete(name=' ', labels = y_labels$predictors_f, breaks=y_labels$var_f) +
#   guides(fill = guide_legend(override.aes = list(shape = 16))) + 
#   xlab('Local Coefficient') +
#   theme_classic() +
#   facet_grid(. ~ transport_f, scale="free_x") +
#   geom_vline(xintercept=c(0,0), linetype="dotted") +
#   theme(legend.position = c('bottom'), text = element_text(colour="black", size=20, family="Times New Roman"))

# ggsave(paste('Spatial_Emissions/outputs/GWR/local_coeffs_plots/ridges_all.png', sep='_'))

all_data$predictors_f = factor(all_data$predictors, levels=c('Income',
                                                             'Public Transport Density',
                                                             'Pop. limited in day-to-day activities',
                                                             'Pop. aged 65 or older',
                                                             'Pop. aged 14 or younger',
                                                             'Pop. identifying as BAME',
                                                             'Distance to workplace'))


y_labels <- all_data %>% select(predictors_f) %>% distinct() %>% arrange()

ggplot() +
  geom_density_ridges_gradient(data=all_data, aes(y=income_controlled, x=local_coeffs, fill=inc)) +
  scale_fill_manual(name = '', values = my_cols$colours) +
  scale_y_discrete(name=' ', labels = c('', '')) +
  guides(fill = guide_legend(override.aes = list(shape = 16))) + 
  ylab('') +
  xlab('Local Coefficient') +
  theme_classic() +
  facet_grid(predictors_f ~ transport_f, scale="free", switch = "y") +
  #facet_grid(transport_f ~ predictors_f, scale="free") +
  geom_vline(xintercept=c(0,0), linetype="dotted") +
  theme(legend.position = c('bottom'), text = element_text(colour="black", size=20, family="Times New Roman"),
        strip.text.y.left = element_text(angle = 0), strip.background = element_blank())

ggsave(paste('Spatial_Emissions/outputs/GWR/local_coeffs_plots/ridges_all_2.png', sep='_'))

for (item in y_labels$predictors_f){
  temp <- all_data %>% filter(predictors_f == item)
  ggplot() +
    geom_density_ridges_gradient(data=temp, aes(y=inc, x=local_coeffs, fill=inc)) +
    scale_fill_manual(name = '', values = my_cols$colours) +
    scale_y_discrete(name=' ', labels = c(item, '')) +
    guides(fill = guide_legend(override.aes = list(shape = 16))) + 
    ylab('') +
    xlab('Local Coefficient') +
    theme_classic() +
    facet_grid(. ~ transport_f, scale="free") +
    #facet_grid(transport_f ~ predictors_f, scale="free") +
    geom_vline(xintercept=c(0,0), linetype="dotted") +
    theme(legend.position = c('bottom'), text = element_text(colour="black", size=20, family="Times New Roman"))
  
  ggsave(paste('Spatial_Emissions/outputs/GWR/local_coeffs_plots/ridges', item, '.png', sep='_'))
  
}
