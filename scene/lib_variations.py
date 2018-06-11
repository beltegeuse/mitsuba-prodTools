import os, sys, optparse, shutil

# Read the options
parser = optparse.OptionParser()
parser.add_option('-i','--input', help='input root path (directory + scene name)')
parser.add_option('-r','--remove', help='remove files not used for variation', default=False, action="store_true")
parser.add_option('-c','--config', help='config file')
(opts, args) = parser.parse_args()

import glob
import xml.etree.ElementTree as ET

def xmlEntry(type, name, value):
    return (type,{"name":name,"value":value})

def generateNewXML(xmlFile, listAttr, out):
    # Get XML tree
    tree = ET.parse(xmlFile)
    sceneRoot = tree.getroot()

    # Add the new node inside integrators
    for integratorNode in sceneRoot.iter("integrator"):
        for typeSubAttr, dictSubV in listAttr:
            newNode = ET.SubElement(integratorNode,typeSubAttr, dictSubV)
    
    # Write out the tree
    tree.write(out)

class ConfigVariation:
    def __init__(self, dict):
        self.stealdir = dict["steal"]

    @staticmethod
    def XML(node):
        d = {"steal" : ""}
        for n in node:
            if "TimeSteal" in n.tag:
                d["steal"] = n.attrib["value"]

        return ConfigVariation(d)


    def apply(self, output_dir, techniques):
        if self.stealdir != "":
            complete_dir = output_dir + os.path.sep + self.stealdir + os.path.sep
            for t in techniques:
                if t.timesteal:
                    for ori_tech in t.techniques:
                        ori_time = complete_dir + ori_tech + "_time.csv"
                        new_time = output_dir + os.path.sep + ori_tech + "_" + t.suffix + "_time.csv"
                        shutil.copy(ori_time, new_time)

class Change:
    def __init__(self, techniques, suffix, listAttr, timesteal = False):
        self.techniques = techniques
        self.suffix = suffix
        self.listAttr = listAttr
        self.timesteal = timesteal
        
    @staticmethod
    def XML(node):
        techniques = node.attrib["techniques"].split(";")
        suffix = node.attrib["suffix"]

        timesteal = False
        if "timesteal" in node.attrib:
            timesteal = node.attrib["timesteal"] == "true"

        attribs = []
        for n in node:
            attribs.append(xmlEntry(n.tag, n.attrib["name"], n.attrib["value"]))
        return Change(techniques, suffix, attribs, timesteal)
    
    def apply(self, xml):
        out = xml.replace(".xml", "_"+self.suffix+".xml")
        generateNewXML(xml, self.listAttr, out)
        return (out,out.replace(opts.input+"_","").replace(".xml",""))
    
    def __str__(self):
        s = "[ techniques: "+str(self.techniques)+", suffix: "+str(self.suffix)+"]"
        return s

def loadConfig(configFile):
    # Get XML tree
    tree = ET.parse(configFile)
    sceneRoot = tree.getroot()

    # Get all selected
    print("--- Selected:")
    selectedConfig = []
    for selected in sceneRoot.iter("Selected"):
        selectedConfig.append(selected.attrib["name"])
        print("  *", selected.attrib["name"])
    
    print("--- Changes:")
    changes = []
    for change in sceneRoot.iter("Change"):
        changes.append(Change.XML(change))
        print(changes[-1])
        
    print("--- Delete")
    deleteConfig = []
    for delected in sceneRoot.iter("Deleted"):
        deleteConfig.append(delected.attrib["name"])
        print("  *", delected.attrib["name"])

    config = None
    for n in sceneRoot.iter("Config"):
        print("  *", "Load config...")
        config = ConfigVariation.XML(n)
    
    return (config, selectedConfig, changes, deleteConfig)

# Read config files
config, selected, changes, deletes = loadConfig(opts.config)

# List all xml files
xmls = glob.glob(opts.input+"*.xml")
xmlsLists = []
print("Base remove: "+opts.input+"_")
for xml in xmls:
    base = xml.replace(opts.input+"_","").replace(".xml","")
    xmlsLists.append((xml, base))

if(opts.remove):
    selectedXmlsLists = []
    for xml, base in xmlsLists:
        if base in selected:
            selectedXmlsLists.append((xml, base))
        else:
            print("Remove: ", xml, "(", base, " not in ", str(selected), ")")
            os.remove(xml)
    # Copy ptr
    xmlsLists = selectedXmlsLists

for change in changes:
    for xml, base in xmlsLists:
        if base in change.techniques:
            xmlsLists.append(change.apply(xml))

xmls = glob.glob(opts.input+"*.xml")
xmlsLists = []
for xml in xmls:
    base = xml.replace(opts.input+"_","").replace(".xml","")
    xmlsLists.append((xml, base))
    
for xml, base in xmlsLists:
    if base in deletes:
        print("Delete",xml)
        os.remove(xml)

# --- Final print
xmls = glob.glob(opts.input+"*.xml")
xmlsLists = []
for xml in xmls:
    base = xml.replace(opts.input+"_","").replace(".xml","")
    xmlsLists.append((xml, base))

print("=================")
print("=== Generated ===")
print("=================")

for xml, base in xmlsLists:
    print(" *",base)

if config:
    print("=================")
    print("=== Config ======")
    print("=================")
    output = os.path.sep.join(opts.input.split(os.path.sep)[:-1])
    print(" - output:", output)
    config.apply(output, changes)