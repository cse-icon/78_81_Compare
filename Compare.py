
removedTagNames=[]
def loadRemovedTagNames():
	print "Loading Removed Tag Names"
	f = open("c:\\temp\Removed_Tag_Names.txt")

	for line in f:
		val = line.strip()
		if len(val)>1:
			removedTagNames.append(val)
		print val
	f.close()


def loadTags(strFileName):
	f = open(strFileName,"r")
	
	firstTime = True
	headers = ""
	headerFields=[]
	tags={}
	noRows=0
	for line in f:
		if firstTime:
			headers = line
			headerFields = line.split(",")
			firstTime=False				
		else:
			if line.find(",")>1:
				values = str(line).split(",")
				tags[values[0].strip()]={}
					
				for i in range(1,len(headerFields)):
					tags[values[0]][headerFields[i].strip()]=values[i].strip()
		noRows += 1
#		if noRows>10:
#			break
	return tags
				

fLogFile = open("C:\\temp\compare.log","w")

def log(strMsg):
	now = system.date.now()
	msg = str(now) +chr(9)+strMsg+"\n"
	
	fLogFile.write(msg)

#
# filters per path
# 	- also removes metadata paths and N/A address
#	- and ignored disabled points
def filterTags(tags,strPath):
	replyTags = {}
	for k in tags.keys():
		if strPath in k and "_metadata" not in k:
			address = tags[k]["address"]
			if len(address)>1 and address != "N\A":
				replyTags[k] = tags[k]
			
	return replyTags
def listTags(tags,maxRows=0):
	contents=""
	firstTime=True
	headers="fullPath,"
	currentRow=0
	for k in tags.keys():
		line=k+","
		for f in tags[k]:
			line += str(tags[k][f])+", "
			if firstTime:
				headers += f+", "
		contents += line +"\n"
		firstTime=False
		currentRow += 1
		
		if maxRows>0 and currentRow>maxRows:
			break;
	contents = headers+"\n"+contents
	return contents

def compareAddress(addrOld,addrNew):
	addrOldAcm=""
	# if TlP update 
	if "-" in addrOld:
		parts = addrOld.split("-")
		parts2 = parts[1].split(".")
		addrOldAcm = parts[0]+"."+parts2[1]+":"+parts2[0]
	else:
		addrOldAcm = addrOld
	
	if addrOldAcm==addrNew and len(addrOldAcm)>0:
		return True
	return False

#
# refreshValues - updates tags dict with value,timestamp,quality and enabled flag
#	
def refreshValues(tags,is79):
	readTags = []
	readTags2 = []
	for k in tags.keys():
		provider = tags[k]["tagProvider"]
		tag = provider+k
		if is79:
			readTags.append(tag+"/value")
		else:
			readTags.append(tag)
			
		readTags2.append(tag+".Enabled")
		
	values = system.tag.readBlocking(readTags,30000)
	values2 = system.tag.readBlocking(readTags2,30000)
	currentRow=0
	for k in tags.keys():
		tags[k]["value"] = values[currentRow].value
		tags[k]["quality"] = values[currentRow].quality
		tags[k]["timestamp"]=values[currentRow].timestamp
		tags[k]["enabled"]=values2[currentRow].value
		currentRow += 1



def compareValues(val1,val2):
	try:
		if isinstance(val1,float) or isinstance(val1,int):

			if val2>= val1*0.90 and val2<= val1*1.10:
				newVal2 = "%.2f" % val2
				newVal1 = "%.2f" % val1
				return str(True)+","+newVal1+","+newVal2
			else:
				return str(False)+","+str(val1)+","+str(val2)
		else:
			return str(val1==val2)+","+val1+","+val2
	except:
		return str(False)+","+str(val1)+","+str(val2)

fPrintSummary = open("c:\\temp\sitesummary.csv","w")
fPrintSummary.write("Site,Good,Bad,State,Bad Tags\n")

#
# printSummary - logs detailed summary to standard log, also creates a sitesummary log for 7.9 compare
#
def printSummary(tags,sites):

	mappedTags = []
	for k in tags.keys():
		if "path81" in tags[k]:
			if tags[k]["path81"] != "N/A":
				mappedTags.append(k)
		

	possibleTags = []
	for k in tags.keys():
		if "path81" in tags[k]:
			if tags[k]["path81"] == "N/A":
				possibleTags.append(k)
			
	unknownTags = []
	for k in tags.keys():
		if "path81" not in tags[k]:
			unknownTags.append(k)
			
	log("Mapped")
	noBad = 0
	noGood = 0
	mappedTags.sort()
	badTags=[]
	for k in mappedTags:
		log( "Ok, V("+tags[k]["compare"]+")"+k + "("+tags[k]["address"]+") = " + tags[k]["path81"] )		
		noGood +=1
			
	log("Possible matches ")
	possibleTags.sort()

	for k in possibleTags:
		if "path81_2" in tags[k]:
			log("Ok, V("+tags[k]["compare"]+")" + k + "("+tags[k]["address"]+") = " + tags[k]["path81_2"])
			noGood += 1
		else:
			msg = k+"("+tags[k]["address"]+")"
			if msg not in badTags:
				offset = k.rfind("/")				
				tagName = k[offset+1:]
				
				if tagName in removedTagNames:
					log("Ok, " + k + "("+tags[k]["address"]+") = Not moved to 81! Ignored.")
				else:
					log("Equip?, " + k + "("+tags[k]["address"]+") = " + ";".join(tags[k]["possible"])+","+str(filterTags79[k]["newequipment"]))
					noBad += 1				
				badTags.append(msg)				

	log("Unknown")
	unknownTags.sort()
	for k in unknownTags:
		if "path81_2" in tags[k]:
			log("Ok, V("+tags[k]["compare"]+")"+k + "("+tags[k]["address"]+") = " + tags[k]["path81_2"])
			noGood += 1
		else:
			address = tags[k]["address"]
			if address != "N/A":
				msg = k+"("+tags[k]["address"]+")"
				if msg not in badTags:
					offset = k.rfind("/")				
					tagName = k[offset+1:]
					
					if tagName in removedTagNames:
						log("Ok, " + k + "("+tags[k]["address"]+") = Not moved to 81! Ignored.")						
					else:
						log("Bad!, " + k + "("+tags[k]["address"]+") = " + sites)
						noBad += 1				
					badTags.append(msg)								
				
#	fPrintSummary = open("c:\\temp\sitesummary.csv","a")
	fPrintSummary.write(sites+",")
	fPrintSummary.write(str(noGood)+",")
	fPrintSummary.write(str(noBad)+",")
	if noGood==0:
		fPrintSummary.write("Failed!,")
	elif noBad==0:
		fPrintSummary.write("Perfect!,")
	elif noBad <5:
		fPrintSummary.write("Close,")
	else :
		fPrintSummary.write("Needs work,")
	
	fPrintSummary.write("\n")	
	


fPrintSummary2 = open("c:\\temp\sitesummary81.csv","w")
fPrintSummary2.write("Site,Good,Bad,Completion,Bad Tags\n")
fPrintSummary2.close()

fCompare2 = open("c:\\temp\81compare.log","w")

def logf(f,strMsg):
	now = system.date.now()
	msg = str(now) +chr(9)+strMsg+"\n"
	
	f.write(msg)	
#
# printSummary81 - logs detailed summary to standard log, also creates a sitesummary log for 81 compare
#
def printSummary81(tags,sites):

	mappedTags = []
	for k in tags.keys():
		if "path79" in tags[k]:
			if tags[k]["path79"] != "N/A":
				mappedTags.append(k)
		

	possibleTags = []
	for k in tags.keys():
		if "path79" in tags[k]:
			if tags[k]["path79"] == "N/A":
				possibleTags.append(k)
			
	unknownTags = []
	for k in tags.keys():
		if "path79" not in tags[k]:
			unknownTags.append(k)
			
	logf(fCompare2,"81 Mapped")
	noBad = 0
	noGood = 0
	mappedTags.sort()
	badTags = []
	for k in mappedTags:
		fCompare2.write( "Ok, "+k + "("+tags[k]["address"]+") = " + tags[k]["path79"] )		
		noGood +=1
			
	logf(fCompare2,"81 Possible matches ")
	possibleTags.sort()

	for k in possibleTags:
		if "path79_2" in tags[k]:
			logf(fCompare2,"Ok, " + k + "("+tags[k]["address"]+") = " + tags[k]["path79_2"])
			noGood += 1
		else:
			msg = k+"("+tags[k]["address"]+")"
			if msg not in badTags:
				logf(fCompare2,"?, " + k + "("+tags[k]["address"]+") = " + tags[k]["possible"])
				noBad += 1				
				badTags.append(msg)								

	logf(fCompare2,"81 Unknown")
	unknownTags.sort()
	for k in unknownTags:
		if "path79_2" in tags[k]:
			logf(fCompare2,"Ok, "+k + "("+tags[k]["address"]+") = " + tags[k]["path79_2"])
			noGood += 1
		else:
			address = tags[k]["address"]
			if address != "N/A":
				msg = k+"("+tags[k]["address"]+")"
				if msg not in badTags:
					logf(fCompare2,"Bad, " + k + "("+tags[k]["address"]+") = " + tags[k]["address"])
					noBad += 1				
					badTags.append(msg)												
	fPrintSummary2 = open("c:\\temp\sitesummary81.csv","a")
	fPrintSummary2.write("81 "+sites+",")
	fPrintSummary2.write(str(noGood)+",")
	fPrintSummary2.write(str(noBad)+",")
	if noGood==0:
		fPrintSummary2.write("Failed!,")
	elif noBad==0:
		fPrintSummary2.write("Perfect!,")
	elif noBad <5:
		fPrintSummary2.write("Close,")
	else :
		fPrintSummary2.write("Needs work,")
	fPrintSummary2.write(";".join(badTags)+"\n")
	
	
	fPrintSummary2.close()
#
# findPathOldAddress - will find selected address in supplied tags, note only returns 1!
#
def findPathOldAddress(address,tags):
	reply=""
	for k in tags.keys():
		newAddress = tags[k]["address"]
		if len(newAddress)>1:
			if compareAddress(address,newAddress):
				return k
	return reply

def findPathNewAddress(address,tags):
	reply=""
	acmCmds = ["ConnectString<C1>","TotalPctGoodPolls","LastPollSuccessTimeUTC","Demand"]
	if address in acmCmds:
		return "ACM: "+address
	for k in tags.keys():
		newAddress = tags[k]["address"]
		if len(newAddress)>1:
			if compareAddress(newAddress,address):
				return k
	return reply
	
	
tagxref={}
def loadTagXref():
	query = "select tag_path_old,tag_path_new,address_new from vw_ign_tagxref where tag_path_old not like '%plunger%'"
	dataset = system.db.runPrepQuery(query, [], "scada_reporting")
	for i in range(dataset.getRowCount()):
		oldPath = dataset.getValueAt(i,0)
		newPath = dataset.getValueAt(i,1)
		address = dataset.getValueAt(i,2)
		offset = oldPath.find("]")
		oldPath = oldPath[offset+1:].replace("/value","")
		
		if oldPath is None:
			continue
			
		if oldPath not in tagxref:
			tagxref[oldPath]=[]	
			
		if newPath is not None:
			tagxref[oldPath].append(str(newPath)+"("+str(address)+")")	
			

#
# process79to81 - will process tags for 1 site, sites contains 79 and 81 path combined
#
def process79To81(filterTags79,filterTag81,sites):
	# load possible tags paths
	
	
	# Add new equipment path to tags
	
	# Load equipment paths for site
	padId = filterTags79.keys()[0]
	offset = padId.find("/")
	padId = padId[:offset+1]





		
#		exists = system.tag.exists(newPath)
#		strExists = "(N)"
#		if exists:
#			strExists = "(Y)"
		
	query = "select TagPathOld,TagPathNew from vw_ign_equipmentxref where TagPathOld like ?"
	dataset = system.db.runPrepQuery(query, [padId+"%"], "scada_reporting")
	
	equipmentData = {}
	equipmentData2={}
	for i in range(dataset.getRowCount()):
		oldPath = dataset.getValueAt(i,0)
		newPath = dataset.getValueAt(i,1)
		equipmentData[oldPath]=newPath
		equipmentData2[newPath]=oldPath
	
	
	# apply equipment info to tags
	equipmentPaths=[]
	equipmentPaths2=[]
	mappedPoints=0
	unmappedPoints=0
	for k in filterTags79.keys():
		offset = k.rfind("/")
		oldPath = k[:offset]
		oldPath = oldPath.replace("/meter_details","")
		oldPath = oldPath.replace("/meter_data","")
		
		if oldPath in equipmentData:
			filterTags79[k]["newequipment"]=equipmentData[oldPath]
			if equipmentData[oldPath] not in equipmentPaths:
				equipmentPaths.append(equipmentData[oldPath])
			mappedPoints += 1
		else:
			filterTags79[k]["newequipment"]="N/A"
#			print k+", " + filterTags79[k]["address"]
			unmappedPoints +=1
			
#	print "Equipment Points " + str(mappedPoints)
#	print "Non Equipment    " + str(unmappedPoints)
	
	# check points for each equipment path with address
	for ep in equipmentPaths:
		for k in filterTags79.keys():
			if filterTags79[k]["newequipment"]==ep:
				match=False
				possibleTags=""
				for k2 in filterTags81.keys():					
					offset = k2.rfind("/")
					path2 = k2[:offset]
					if path2==ep:
						if len(filterTags79[k]["address"])>0 and compareAddress(filterTags79[k]["address"],filterTags81[k2]["address"]):
#							print "Got Match " + k	
							filterTags79[k]["path81"]=k2
							v1 = filterTags79[k]["value"]
							v2 = filterTags81[k2]["value"]
							filterTags79[k]["compare"]=compareValues(v1,v2)
							match=True
						possibleTags += k2+","
				if match==False:
					filterTags79[k]["path81"]="N/A"
					if k in tagxref:
						filterTags79[k]["possible"]=tagxref[k]
					else:
						filterTags79[k]["possible"]=[]
					newPath = findPathOldAddress(filterTags79[k]["address"],filterTags81)
					if len(newPath)>1:						
						filterTags79[k]["path81_2"]=newPath
						v1 = filterTags79[k]["value"]
						v2 = filterTags81[newPath]["value"]
						filterTags79[k]["compare"]=compareValues(v1,v2)						
					
					
	
	for k in filterTags79.keys():
		if	"path81" not in filterTags79[k]:
			address = filterTags79[k]["address"]
			if k in tagxref:
				filterTags79[k]["possible"]=tagxref[k]
			else:
				filterTags79[k]["possible"]=[]		
				
			if len(address)>1:
				newPath = findPathOldAddress(address,filterTags81)
				if len(newPath)>1:
					filterTags79[k]["path81_2"]=newPath
					v1 = filterTags79[k]["value"]
					v2 = filterTags81[newPath]["value"]
					filterTags79[k]["compare"]=compareValues(v1,v2)
				elif len(filterTags79[k]["possible"])>0:
					filterTags79[k]["path81_2"]=filterTags79[k]["possible"][0]
					filterTags79[k]["compare"]="No Compare"
				
			
				
			
				
				
					
					
	printSummary(filterTags79,sites)
	
	
	
	# Handle 81 to 79
	allPadTags79= filterTags(tags79,padId)
	
	# apply equipment info to 81 tags
	equipmentPaths2=[]
	mappedPoints=0
	unmappedPoints=0
	for k in filterTags81.keys():
		offset = k.rfind("/")
		oldPath = k[:offset]
			
		if oldPath in equipmentData2:
			filterTags81[k]["oldequipment"]=equipmentData2[oldPath]
			if equipmentData2[oldPath] not in equipmentPaths2:
				equipmentPaths2.append(equipmentData2[oldPath])
			mappedPoints += 1
		else:
			filterTags81[k]["oldequipment"]="N/A"
#			print k+", " + filterTags79[k]["address"]
			unmappedPoints +=1	
			
	# check points for each equipment path with address
	for ep in equipmentPaths2:
		for k in filterTags81.keys():
			if filterTags81[k]["oldequipment"]==ep:
				match=False
				possibleTags=""
				for k2 in filterTags79.keys():					
					offset = k2.rfind("/")
					path2 = k2[:offset]
					if path2==ep:
						if len(filterTags81[k]["address"])>0 and compareAddress(filterTags79[k2]["address"],filterTags81[k]["address"]):
#							print "Got Match " + k	
							filterTags81[k]["path79"]=k2
							match=True
						possibleTags += k2+","
				if match==False:
					filterTags81[k]["path79"]="N/A"
					filterTags81[k]["possible"]=possibleTags
#					newPath = findPathNewAddress(filterTags81[k]["address"],filterTags79)
					newPath = findPathNewAddress(filterTags81[k]["address"],allPadTags79)					
					if len(newPath)>1:						
						filterTags81[k]["path79_2"]=newPath
					
					
	
	for k in filterTags81.keys():
		if	"path79" not in filterTags81[k]:
			address = filterTags81[k]["address"]
			if len(address)>1:
#				newPath = findPathNewAddress(address,filterTags79)
				newPath = findPathNewAddress(address,allPadTags79)
				
				if len(newPath)>1:
					filterTags81[k]["path79_2"]=newPath
					
	printSummary81(filterTags81,sites)							




fDeleteLog = open("C:\\temp\deleted.csv","w")
fDeleteLog.close()

#
# clearDisabledPoints - will remove tags from dictionary if "enabled" = False
#
def clearDisabledPoints(tags):
	fDeleteLog = open("C:\\temp\deleted.csv","a")
	for k in tags.keys():
		enabled = tags[k]["enabled"]
		if enabled == False:
			fDeleteLog.write(k +"\n")
			del tags[k]
	fDeleteLog.close()
	
	
	
	
	
#
# -----------------------------------  Start of Main -----------------------------------------
tags81 = loadTags("C:\\temp\81_tags.csv")

log("Loaded "+str(len(tags81))+" from C:\\temp\81_tags.csv")
if len(tags81)<10:
	print tags81
tags79 = loadTags("c:\\temp\combined79_tags_tpl.csv")


log("Loaded 79 and 81 tags")

# Run through sites
query = "select tag_path_old,tag_path_new,short_description,property_number from vw_ign_sitexref"
dataset = system.db.runQuery(query, "scada_reporting")
print dataset.getRowCount()
rowCount=0
firstTime=True
lastPadName=""
padTagCount=0
loadTagXref()
loadRemovedTagNames()

for siteOffset in range(dataset.getRowCount()):
	old_path = str(dataset.getValueAt(siteOffset,0))
	new_path = str(dataset.getValueAt(siteOffset,1))
	description = str(dataset.getValueAt(siteOffset,2))
	
	log("Processing "+description+";"+new_path)
	logf(fCompare2,msg)
	filterTags79=filterTags(tags79,old_path)
	if len(filterTags79)>0:
		refreshValues(filterTags79,True)
#		print listTags(filterTags79,10)
		clearDisabledPoints(filterTags79)
		
	msg = "filterTags79 Count "+str(len(filterTags79))
	log(msg)
	logf(fCompare2,msg)

	filterTags81=filterTags(tags81,new_path)

	
	if len(filterTags81)>0:
		refreshValues(filterTags81,False)
		clearDisabledPoints(filterTags81)
		
	msg = "filterTags81 Count "+str(len(filterTags81))
	log(msg)
	logf(fCompare2,msg)
	
	offset = old_path.find("/")
	padName = old_path[:offset]	
	if firstTime:
		oldPadName = padName
		padTagCount = len(filterTags79)
	else:
		if padName <> oldPadName:
			fPrintSummary.write("Pad Total ("+oldPadName+"):"+str(padTagCount)+"\n")
			padTagCount = len(filterTags79)
			oldPadName = padName
		else:
			padTagCount += len(filterTags79)
	firstTime=False
	
	if len(filterTags79)>1 and len(filterTags81)>1:
		process79To81(filterTags79,filterTags81,old_path+";"+new_path)
	else:
		msg= "Unable to process " + old_path +";"+new_path
		print msg
		log(msg)
		fPrintSummary.write(old_path+";"+new_path+",")
		fPrintSummary.write(str(len(filterTags79))+",")
		fPrintSummary.write(str(len(filterTags81))+",")
		fPrintSummary.write("Unable to Process!\n")
	
	rowCount +=1
	if rowCount%50==0:
		print rowCount
#	if rowCount>5:
#		break
		
#	print listTags(filterTags79)

	
fLogFile.close()
fCompare2.close()
fPrintSummary.close()