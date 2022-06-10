library(ggridges)
library(tidyverse)
library(purrr)
library(tm)

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
  cbind(data_frame('predictors' = c('Public Transport Density', 'Pop. ltd in day-to-day act.',
                                    'Pop. aged 65 or older', 'Pop. aged 14 or younger', 'Pop. identifying as BAME',
                                    'Distance to workplace', 'Income'))) 
order$predictors_f = factor(order$predictors, levels=c('Distance to workplace', 
                                                       'Pop. identifying as BAME',
                                                       'Pop. aged 14 or younger',
                                                       'Pop. aged 65 or older',
                                                       'Pop. ltd in day-to-day act.',
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
                                                             'Pop. ltd in day-to-day act.',
                                                             'Pop. aged 65 or older',
                                                             'Pop. aged 14 or younger',
                                                             'Pop. identifying as BAME',
                                                             'Distance to workplace'))


y_labels <- all_data %>% select(predictors_f) %>% distinct() %>% arrange()

# ggplot() +
#   geom_density_ridges_gradient(data=all_data, aes(y=income_controlled, x=local_coeffs, fill=inc)) +
#   scale_fill_manual(name = '', values = my_cols$colours) +
#   scale_y_discrete(name=' ', labels = c('', '')) +
#   guides(fill = guide_legend(override.aes = list(shape = 16))) + 
#   ylab('') +
#   xlab('Local Coefficient') +
#   theme_classic() +
#   facet_grid(predictors_f ~ transport_f, scale="free", switch = "y") +
#   #facet_grid(transport_f ~ predictors_f, scale="free") +
#   geom_vline(xintercept=c(0,0), linetype="dotted") +
#   theme(legend.position = c('bottom'), text = element_text(colour="black", size=20, family="Times New Roman"),
#         strip.text.y.left = element_text(angle = 0), strip.background = element_blank())
# 
# ggsave(paste('Spatial_Emissions/outputs/GWR/local_coeffs_plots/ridges_all_2.png', sep='_'))
# 
# for (item in y_labels$predictors_f){
#   temp <- all_data %>% filter(predictors_f == item)
#   ggplot() +
#     geom_density_ridges_gradient(data=temp, aes(y=inc, x=local_coeffs, fill=inc)) +
#     scale_fill_manual(name = '', values = my_cols$colours) +
#     scale_y_discrete(name=' ', labels = c(item, '')) +
#     guides(fill = guide_legend(override.aes = list(shape = 16))) + 
#     ylab('') +
#     xlab('Local Coefficient') +
#     theme_classic() +
#     facet_grid(. ~ transport_f, scale="free") +
#     #facet_grid(transport_f ~ predictors_f, scale="free") +
#     geom_vline(xintercept=c(0,0), linetype="dotted") +
#     theme(legend.position = c('bottom'), text = element_text(colour="black", size=20, family="Times New Roman"))
#   
#   ggsave(paste('Spatial_Emissions/outputs/GWR/local_coeffs_plots/ridges', item, '.png', sep='_'))
#   
# }

# by mode of transport
global <- read.csv('Spatial_Emissions/outputs/GWR/summary_table.csv', skip=1, header = TRUE) %>% 
  filter(Income.controlled == 'Yes') %>%
  mutate('pred' = ifelse(Pred. == 'Income', 'totalinc', 'NA'),
         'pred' = ifelse(Pred. == 'Public Transport Density', 'AI2015ln', pred),
         'pred' = ifelse(Pred. == 'Pop. limited in day-to-day activities', 'lim', pred),
         'pred' = ifelse(Pred. == 'Pop. aged 65 or older', 'pop65', pred),
         'pred' = ifelse(Pred. == 'Pop. aged 14 or younger', 'pop14', pred),
         'pred' = ifelse(Pred. == 'Pop. identifying as BAME', 'bame', pred),
         'pred' = ifelse(Pred. == 'Distance to workplace', 'totalwork', pred)) %>%
  mutate('global_pval' = 'p ≥ 0.05',
         'global_pval' = ifelse(predictor.1 == '*', 'p < 0.05', global_pval),
         'global_pval' = ifelse(predictor.1 == '**', 'p < 0.01', global_pval)) %>%
  select(c('DV', 'pred', 'predictor', 'global_pval', 'AIC'))
names(global) <- c('transport', 'pred', 'global_coef', 'global_pval', 'AIC')

global$global_pval_f = factor(global$global_pval, levels=c('p ≥ 0.05', 'p < 0.05', 'p < 0.01'))

colours <- data_frame(global_pval = levels(global$global_pval_f)) %>% 
  arrange() %>% 
  cbind(data_frame(pval_cols = c('#D5E4F0', '#ECB89B', '#B54642')))

global <- global %>% left_join(colours, by='global_pval')

all_data <- all_data %>% filter(inc == 'Income controlled') %>% left_join(global, by=c('transport', 'pred'))

# limit_list <- c(15, 10, 1.5, 0.5, 0.75)
# transport_list <- all_data %>% arrange(transport_f) %>% select(transport) %>% distinct()
# for (i in seq(1, length(transport_list$transport))){
#   item <- transport_list$transport[i]
#   temp <- all_data %>% filter(transport == item) %>% filter(inc == 'Income controlled')
#   ggplot() +
#     geom_density_ridges_gradient(data=temp, aes(y=predictors_f, x=local_coeffs), fill="lightgray") + # "#F1B593" "#C54A43"
#     guides(fill = guide_legend(override.aes = list(shape = 16))) + 
#     scale_y_discrete(limits = rev(levels(temp$predictors_f)), position = "right") + #, position = "right"
#     ylab('') +
#     xlab(' ') +
#     xlim(-1*limit_list[i], limit_list[i]) +
#     theme_classic() +
#     #facet_grid(transport_f ~ predictors_f, scale="free") +
#     geom_vline(xintercept=c(0,0), linetype="dotted") +
#     theme(text = element_text(colour="black", size=20, family="Times New Roman"))
#   
#   ggsave(paste('Spatial_Emissions/outputs/GWR/local_coeffs_plots/ridges', removePunctuation(item), '.png', sep='_'))
# }

# Separate income
# income plot
temp <- all_data %>% filter(predictors == 'Income') 
global_coef_fig <- temp %>% select(transport_f, global_coef, global_pval_f, pval_cols) %>% distinct()
colour <- global_coef_fig %>% arrange(global_pval_f) %>% select(pval_cols) %>% distinct()
labels <- temp %>% select(transport_f, AIC) %>% distinct() %>% arrange(transport_f) %>%
  mutate(AIC = paste(round(AIC, 0)))
ggplot() +
  geom_density_ridges_gradient(data=temp, aes(y=transport_f, x=local_coeffs), fill="lightgray") + # "#F1B593" "#C54A43"
  scale_y_discrete(limits = rev(levels(temp$transport_f))) + #, position = "right") + 
  guides(fill = guide_legend(override.aes = list(shape = 16))) +
  ylab('') +
  xlab(' ') +
  xlim(-18, 13) +
  theme_classic() +
  #facet_grid(transport_f ~ predictors_f, scale="free") +
  geom_vline(xintercept=c(0,0), linetype="dotted") +
  coord_cartesian(xlim = c(-4, 13), clip = "off") + 
  # add global coef.
  geom_point(data = global_coef_fig, aes(y=transport_f, x=global_coef, fill=global_pval_f),
             colour="black", pch=21, size = 5, inherit.aes = FALSE) +
  scale_fill_manual(values=colour$pval_cols, name='Global coef.') +
  #geom_text(aes(x=-1.6*4, y=labels$transport_f, label=labels$AIC), 
  #          colour="black", size=9, family="Times New Roman") +
  #geom_text(aes(x=-3*4, y=labels$transport_f, label=labels$transport_f), 
  #          colour="black", size=9, family="Times New Roman", hjust = 0) +
  theme(text = element_text(colour="black", size=30, family="Times New Roman"),
        plot.margin = unit(c(0, 0, 0, 0), "lines"))
ggsave('Spatial_Emissions/outputs/GWR/local_coeffs_plots/ridges_incomeonly.png')


# other prdictors
limit_list <- c(15, 20, 2.6, 0.8, 1.2)
transport_list <- all_data %>% arrange(transport_f) %>% select(transport) %>% distinct()
for (i in seq(1, length(transport_list$transport))){
  item <- transport_list$transport[i]
  temp <- all_data %>% filter(transport == item) %>% filter(predictors != 'Income')
  global_coef_fig <- temp %>% select(predictors_f, global_coef, global_pval_f, pval_cols) %>% distinct()
  colour <- global_coef_fig %>% arrange(global_pval_f) %>% select(pval_cols) %>% distinct()
  labels <- temp %>% select(predictors_f, AIC) %>% distinct() %>% arrange(predictors_f) %>%
    mutate(AIC = paste(round(AIC, 0)))
  ggplot() +
    geom_density_ridges_gradient(data=temp, aes(y=predictors_f, x=local_coeffs), fill="lightgray") + # "#F1B593" "#C54A43"
    scale_y_discrete(limits = rev(levels(temp$predictors_f)[2:7])) + #, position = "right") + 
    ylab('') +
    xlab(' ') +
    xlim(-3*limit_list[i], limit_list[i]) +
    theme_classic() +
    #facet_grid(transport_f ~ predictors_f, scale="free") +
    geom_vline(xintercept=c(0,0), linetype="dotted") +
    coord_cartesian(xlim=c(-1*limit_list[i], limit_list[i]), clip = "off") +
    # add global coef.
    geom_point(data = global_coef_fig, aes(y=predictors_f, x=global_coef, fill=global_pval_f),
               colour="black", pch=21, size = 5, inherit.aes = FALSE) +
    scale_fill_manual(values=colour$pval_cols, name='Global coef.') +
    # CHANGE FONT!!
    #geom_text(aes(x=-1.35*limit_list[i], y=labels$predictors_f, label=labels$AIC), 
    #          colour="black", size=9, family="Times New Roman")  +
    #geom_text(aes(x=-2.6*limit_list[i], y=labels$predictors_f, label=labels$predictors_f), 
    #          colour="black", size=9, family="Times New Roman", hjust = 0) +
    theme(text = element_text(colour="black", size=30, family="Times New Roman"),
          plot.margin = unit(c(1, 0, 0, 0), "lines"))
  ggsave(paste('Spatial_Emissions/outputs/GWR/local_coeffs_plots/ridges', removePunctuation(item), '.png', sep='_'))
}
