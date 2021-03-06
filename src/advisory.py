"""
Aquest modul s'encarrega de contenir el format dels avisos de cendra volcanica
(Volcanic Ash Advisory - VAA). Proveeix dels recursos necessaris per extreure
totes les dades que formen una mostra a partir d'un text en format VAA.
* fields: construeix una llista amb els noms de tots els camps els valors dels
  quals constitueixen una mostra.
* parse: forma una llista amb els valors de la mostra que construim a partir
  d'un VAA.
  Consideracions: aquest metode retornara una mostra si el VAA conte observacio
  i es identificable del del satel.lit; en altre cas, retornara []-
  Si algun dels parametres no es troben en el format esperat i per tant no es poden
  extreure, el seu valor es NA.
  En el cas de les prediccions, es contempla el cas de que sigui que no s'espera
  cendra ("NO ASH EXPECTED"), i si falta informacio pot ser que sigui perque simplement
  no hi ha, llavors els atributs seran 'None'
     
"""

import re

def fields():
    names = ["VA_DATE","VOLCANO_NAME","VOLCANO_ID",
             "OBS_DATE","OBS_LOWALT","OBS_HIGHALT","OBS_CONTOUR",
             "FCST+6_DATE","FCST+6_LOWALT","FCST+6_HIGHALT","FCST+6_CONTOUR",
             "FCST+12_DATE","FCST+12_LOWALT","FCST+12_HIGHALT","FCST+12_CONTOUR",
             "FCST+18_DATE","FCST+18_LOWALT","FCST+18_HIGHALT","FCST+18_CONTOUR"]
    return names

def parse(text, link):
    # Check if we want this advisory, i.e. there is observed cloud
    token = re.findall("OBS VA CLD.*$",text,re.MULTILINE)
    if not(token):#there is no observation
        print("WARNING: there is no observation in advisory '"+
                  link +"'. It is discarded\n")
        return []
        # Observation is not identifiable
    if re.match("^.*NOT IDENTIFIABLE.*$",token[0]):
        print("WARNING: cloud not identifiable in advisory '"+
                  link +"'. It is discarded\n")
        return []
        # There is not information about observation (empty OBS VA CLD)
    token=re.split(r'\W+', token[0])
    if len(token)==3:
        return []
    ## Parse required information
    advisory=[]
    # Advisory date. Format: YYYYMMDDHHMM
    token = re.findall("^DTG.*$",text,re.MULTILINE)
    if token:
        token = re.findall("[0-9]+",token[0])
        if (len(token)==2)&(len(token[0]+token[1])==12):
            advisory.append(token[0]+token[1])
            yearmonth = token[0][:6]
        else:
            print("WARNING: unexpected date format in advisory '"+
                  link +"'. It is set as 'NA'\n")
            advisory.append('NA')
    else:
        print("WARNING: date is missing in advisory '"+
              link +"'. It is set as 'NA'\n")
        advisory.append('NA')
    
        # Volcano name and ID
    token = re.findall("^VOLCANO.*$",text,re.MULTILINE)
    if token:
        token=re.split(r'\W+', token[0])
        if (len(token)>1):
            advisory.append(token[1])
            # If there is ID, it must be number
            if (len(token)>2)&(token[2].isdigit()):
                advisory.append(token[2])
            else:
                print("WARNING: there is no volcano ID in advisory '" +
                      link + "'. It is set as 'NA'\n")
                advisory.append('NA')
        else:
            # There is no volcano data
            print("WARNING: unkwnown volcano name and ID are missing in advisory '"+
                  link + "'. They are set as 'NA'\n")
            advisory.extend(['NA'] * 2)

    else:
        print("WARNING: volcano name and ID are missing in advisory '" + 
              link + "'. They are set as 'NA'\n")
        advisory.append('NA')
    # Observation date
    token = re.findall("OBS VA DTG.*$",text,re.MULTILINE)
    if (token):
        # In token we will have day and hour. Year and month is recover from advisory date.
        token = re.findall("[0-9]+",token[0])
        if (len(token)==2):
            advisory.append(yearmonth + token[0] + token[1])
        else:
            advisory.append('NA')
    else:
        print("WARNING: observation date is missing in advisory '" + 
              link + "'. It is set as 'NA'\n")
        advisory.append('NA')
    # Observed cloud.
    # We will extract: low alt, high alt, cloud polygon
    # Expected: "OBS VA CLD: FLXX/FLXX lat1 lon1 - lat2 lon2 - lat3 lon3...
    # And it can be more than one line
    lines = text.splitlines()
    for idx in range(0,len(lines),1):
        if lines[idx].find("OBS VA CLD",0,12)>-1:
            break
    i=1
    while lines[idx+i] != '':
        lines[idx] += ' ' + lines[idx+i]
        i+=1
    
    token=re.split(r'\W+', lines[idx])
    # At least cloud needs to be defined by 3 points
    if len(token) < 11:
        print("WARNING: observation cloud is missing in advisory '" + 
          link + "'. It will be discarded\n")
        return []
    else:
        advisory.append( token[3] )
        advisory.append( token[4] )
        polygon=''
        size = len(token)
        if (size%2 ==0):
            size -= 1
        for idx in range(5,size,2):
            if re.match("[S,N]*[0-9]",token[idx]):
                polygon += token[idx]+token[idx+1]
            else:
                break
        if len(polygon)==0:
            polygon='NA'
        advisory.append(polygon)
    # Forecasts
    # Expected: "FCST VA CLD +xHR: DD/HHMMZ FLXX/FLXX lat1 lon1 - lat2 lon2 - lat3 lon3...
    # It can be several lines in text
    # We will extract for each forecast: date, low alt, high alt, cloud polygon
    patterns=["FCST VA CLD +6HR","FCST VA CLD +12HR","FCST VA CLD +18HR"]
    for pidx in range(0,3,1):
        lines = text.splitlines()
        found = False
        for idx in range(0,len(lines),1):
            if lines[idx].find(patterns[pidx],0,20)>-1:
                found = True
                break
        if not found:# There is no FCST
            advisory.extend(['None'] * 4)
            continue
        
        i=1
        while lines[idx+i] != '':
            lines[idx] += ' ' + lines[idx+i]
            i+=1
            
        token=re.split(r'\W+', lines[idx])
        if (len(token) < 5):# FCST is empty
            advisory.extend(['None'] * 4)
            continue
        # Parse forecast date
        if (not(token[4].isdigit()))|(not(token[5][:-1].isdigit())):
            advisory.append('NA')
        else:
            advisory.append(yearmonth + token[4] + token[5][:-1])
        # Parse forecast cloud
        if ((re.match("^.*NO VA EXP.*$",lines[idx])) is not None)|((re.match("^.*NO ASH EXP.*$",lines[idx])) is not None):
            advisory.extend(['None'] * 2)
            advisory.append('NO ASH')
        else:
            # At least cloud needs to be defined by 3 points
            if len(token) < 14:
                advisory.extend(['None'] * 3)
            else:
                advisory.append( token[6] )
                advisory.append( token[7] )
                polygon=''
                size = len(token)
                if (size%2 ==1):
                    size -= 1
                for idx in range(8,size,2):
                    # Check the list stars with latitude coordinate
                    if re.match("[S,N]*[0-9]",token[idx]):
                        polygon += token[idx]+token[idx+1]
                    else:
                        break
                if len(polygon)==0:
                    polygon='NA'
                advisory.append(polygon)
            
    if len(advisory)!=19:
        print("ERROR: No all fields set in advisory\n")
    
    return advisory