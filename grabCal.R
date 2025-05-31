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
  
  mainDF <- data.frame()
  
  for (k in 1:length(methodDetails[[1]])){
    temp2 <- setNames(methodDetails[[1]][k], methodDetails[[1]][k]$para_vec_double$.attrs[[1]])
    temp2 <- as.data.frame(t(as.data.frame(temp2)))
    if (ncol(mainDF) == 0){
      mainDF <- temp2
    }
    
    if (ncol(mainDF) > ncol(temp2)){
      temp2 <- cbind(permname=rownames(temp2), temp2)
      if (colnames(temp2)[2] != "polarity"){
        mainDF <- rbind(mainDF, temp2)
      }
    }
    
    if (ncol(mainDF) == ncol(temp2)){
      if (colnames(temp2)[2] != "polarity"){
      mainDF <- rbind(mainDF, temp2)
      }
      }
    }
  
  rownames(mainDF) <- NULL
  
  selectPermnames <- c("LastCalibrationDate",
                       "Calibration_LastCalibrationDate",
                       "Calibration_LastCalibrationCurrentMass.entry_double",
                       "Calibration_LastCalibrationMassError.entry_double",
                       "Calibration_LastCalibrationMassIntensity.entry_double",
                       "Calibration_Score",
                       "Calibration_StdDev",
                       "Calibration_StdDevInPPM",
                       "IMS_Calibration_LastCalibrationDate",
                       "IMS_Calibration_LastCalibrationReferenceMass.entry_double",
                       "IMS_Calibration_LastCalibrationMobilityError.entry_double",
                       "IMS_Calibration_LastCalibrationMassIntensity.entry_double",
                       "IMS_Calibration_LastCalibrationReferenceMassList",
                       "IMS_Calibration_LastCalibrationReferenceMobility.entry_double",
                       "IMS_Calibration_LastCalibrationResultMobility.entry_double",
                       "IMS_Calibration_Score",
                       "IMS_Calibration_StdDev",
                       "Calibration_TOF_CorrectorExtractSetValue",
                       "Calibration_TOF_CorrectorFillSetValue",
                       "Calibration_TOF_DeceleratorSetValue",
                       "Calibration_TOF_DetectorTofSetValue",
                       "Calibration_TOF_ReflectorSetValue",
                       "Calibration_TOF_FlightTubeSetValue",
                       "Calibration_Tof2Score",
                       "Calibration_Tof2StdDev",
                       "Calibration_Tof2StdDevInPPM",
                       "Calibration_Tof2CalC0",
                       "Calibration_Tof2CalC1",
                       "Calibration_Tof2CalC2",
                       "Calibration_TofCalC0",
                       "Calibration_TofCalC1",
                       "Calibration_TofCalC2",
                       "Calibration_Collision_GasSupply_Set",
                       "TOF_DeviceReferenceTemp1",
                       "TOF_DeviceReferenceTemp2")
  
  mainDF_filtered <- mainDF[grep(selectPermnames, mainDF$permname),]
  
  
  for (entry in selectPermnames){
    
    
    
    
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