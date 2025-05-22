library(RSQLite)
library(xml2)
library(XML)
library(tidyverse)
library(magrittr)

# Getting instrument maintenance history from history.sqlite that is also used by Bruker Twinscape
conn <- dbConnect(RSQLite::SQLite(), "C:/Data_analysis/timsTOF/InstrumentHistory/history.sqlite")
dbListTables(conn)
InstrumentParameterHistory <- dbGetQuery(conn, "SELECT * FROM InstrumentParameterHistory")
InstrumentParameterHistory

# Accessing the calibration method file and getting cal values from the xml file

calmeths <- list.files(path = "M:/2025/Brandon/timsTOF/InstrumentHistory")
calmeths <- calmeths[-grep("history.sqlite", calmeths)]
calPaths <- paste0("M:/2025/Brandon/timsTOF/InstrumentHistory/",calmeths)


for (i in 1:length(calmeths)){
  
list2env(
  lapply(setNames(paste0(calPaths[i],"/microTOFQImpacTemAcquisition.method"), calmeths[i]), 
         xml2::read_xml), envir = .GlobalEnv)
  
  temp <- get(calmeths[i]) 
  
  temp %>%
    as_xml_document() %>%
    xmlParse() -> temp
  
  childrenList <- XML::xmlChildren(temp)
  methodList <- xmlToList(childrenList[["root"]][["instrument"]][["qtofimpactemacq"]])
  methodDetails <- methodList[37]
  methodDetailsDF <- as.data.frame(t(as.data.frame(methodDetails)))
                                   
  for (k in 1:length(methodDetails[[1]])){
    temp2 <- setNames(methodDetails[[1]][20], methodDetails[[1]][20]$para_vec_double$.attrs[[1]])
    temp2 <- as.data.frame(t(as.data.frame(temp2)))
    
    # methodDetails[[1]][k]
    
    
  }
  
  
  
  
  
  # 
  # temp %>%
  #   xmlToDataFrame(nodes = getNodeSet(temp, "//root/generalinfo")) %>%
  #   as.data.frame() -> generalinfo
  # 
  # temp %>%
  #   xmlToDataFrame(nodes = getNodeSet(temp, "//root/instrument/qtofimpactemacq")) %>%
  #   as.data.frame() -> test

}



"C:/Data_analysis/timsTOF/InstrumentHistory/20230602T114748/microTOFQImpacTemAcquisition.method"