def GetTagPaths(tagProvider):
	
	filter = {"valueSource":"opc",
			"tagType":"AtomicTag","recursive":True}
	results = system.tag.browse("["+tagProvider+"]",filter)
	tags = {}
	
	for t in results.getResults():
		fullPath = str(t["fullPath"])
		if "_types_" not in fullPath and "PLUNGER" not in fullPath.upper():
			parts=fullPath.split("]")
			tags[parts[1]] = {"tagProvider":parts[0]+"]"}
		
	return tags
def GetProperty(tagPaths,property):
	newTagPaths=[]
	rowCount=0
	for t in tagPaths.keys():
		newTagPaths.append(tagPaths[t]["tagProvider"]+t +"."+property)				
		rowCount += 1
#		if rowCount>10:
#			break
	return system.tag.readBlocking(newTagPaths)
	

def SaveTags(strFileName):
	f = open(strFileName,"w")
	headers = "fullPath,device,long_description,channel,value,quality,timestamp,tagProvider,address"
	f.write(headers+"\n")
	fields = headers.split(",")
	for k in tags.keys():
		line = k+","
		for i in range(1,len(fields)):
			if fields[i] in tags[k]:
				line += tags[k][fields[i]]+","
			else:
				line += ","
		f.write(line[:-1]+"\n")
		
		
	



tags = GetTagPaths("APIGNIO001P")
print len(tags)

opcItemPaths = GetProperty(tags,"opcItemPath")

rowCount=0
tags2={}
for k in tags.keys():
	opcItemPath = str(opcItemPaths[rowCount].value)


	offset = opcItemPath.find(":s=")
	offset2 = opcItemPath.find(".")
	
	# split to device and item
    
	device=""
	address=""
	if offset2>offset:
		device = opcItemPath[offset+3:offset2]
		address = opcItemPath[offset2+1:]
'		print device +","+ address
	tags[k]["device"]=device
	tags[k]["address"]=address

     
	rowCount += 1
	if rowCount % 1000==0:
		print rowCount
#	if rowCount>10:
#		break
SaveTags("c:\\temp\81_tags.csv")
# Save tags