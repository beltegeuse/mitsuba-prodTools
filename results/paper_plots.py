import optparse
import glob
import os
import lib_csv
import matplotlib.pyplot as plt
from pylab import *
import numpy as np
import matplotlib.transforms as transforms
import debug_show
from matplotlib import rc, font_manager
from decimal import *
import xml.etree.ElementTree as ET

class AlgorithmPlot:
    def __init__(self, name, metricBase, style, color, inFocus = True):
        self.name = name
        self.metricBaseName = metricBase
        self.curveStyle = style
        self.color = color
        self.inFocus = inFocus

if __name__=="__main__":
    parser = optparse.OptionParser()
    parser.add_option('-i','--input', help="input directory", default="")
    parser.add_option('-o','--output', help="output pdf name", default="")
    parser.add_option('-e','--errorName', help="type of plot (rmse_time or relative_time)", default="")
    parser.add_option('-t','--timelabel', help='Show time label', default=False, action="store_true")
    parser.add_option('-l','--uselog', help='Use log scale', default=False, action="store_true")
    parser.add_option('-c','--config', help='config', default="")
    (opts, args) = parser.parse_args()
    
    #############################
    ### SETTINGS
    #############################
    isLogLog = opts.uselog
    #errorName = "rmse_time"
    #errorName = "relative_time"
    errorName = opts.errorName

    #### Read config files
    algorithms = []
    tree = ET.parse(opts.config)
    root = tree.getroot()

    for cNode in root.iter('Curve'):
        color = [int(e) for e in cNode.attrib["color"].split(",")]
        algorithms += [
            AlgorithmPlot(cNode.attrib["name"], cNode.attrib["filename"], cNode.attrib["style"], color)
        ]

    extractedData = {}
    maxLenghtData = 0
    print(opts.input)

    # Construct techniques names
    requestedTech = []
    for alg in algorithms:
        requestedTech.append(alg.metricBaseName)

    # Read all the requested techniques
    # And copy the data values
    techniques = debug_show.readAllTechniques(requestedTech, opts.input, 5, False,  basey='_'+errorName+'.csv')
    for alg in algorithms:
        currentTech = None
        for tech in techniques:
            if tech.name == alg.metricBaseName.split(",")[0]:
                currentTech = tech

        (times, values) = (currentTech.x, currentTech.y)
        
        name = alg.name
        extractedData[ name ] = (times,values)
        #maxLenghtData = max(len(data), maxLenghtData)

    # Change the font option
    sizeOfFont = 7.97*3
    fontProperties = {'family':'serif','serif':['Nimbus Roman'],
                      'weight' : 'normal', 'size' : sizeOfFont}
    rc('text', usetex=True)
    rc('font',**fontProperties)
    
    fig = plt.figure(figsize=(4,3), dpi=120) #,dpi=80
    ax = fig.add_subplot(1,1,1)

    # Compute the min and max x/y values
    maxyvalue = -10000
    minyvalue = 10000
    minxvalue = 10000
    maxyvalueFocus = -10000
    for alg in algorithms:
        # Take care only in focus techniques for the window clamping
        data = extractedData[ alg.name ]
        if alg.inFocus:
            maxyvalue = max( maxyvalue, max(data[1]) )
            maxyvalueFocus = max(maxyvalueFocus, max(data[1]) )
        else:
            maxyvalue = max( maxyvalue, max(data[1]) / 10.0 )
        minyvalue = min( minyvalue, min(data[1]) )
        minxvalue = min( minxvalue, min(data[0]) )
    print("MIIN!!!MAX!!!",minyvalue,(minyvalue+maxyvalueFocus)*0.05,maxyvalue)
    minyvalue = 0.0001
    maxyvalue = maxyvalueFocus = 0.01

    #yAxis = [0.0001, 0.001, 0.01, 0.1, 1.0, 10.0] # GPM values
    yAxis = [0.1, 1, 10]
    for cNode in root.iter('yAxis'):
        yAxis = [float(e) for e in cNode.attrib["values"].split(",")] # GVPM values
    print("Read yAxis values:", yAxis)

    xAxis = [60,300,1800]
    for cNode in root.iter('xAxis'):
        xAxis = [float(e) for e in cNode.attrib["values"].split(",")] # GVPM values
    print("Read xAxis values:", xAxis)


    # For all the algorithm
    # Plot them
    for alg in algorithms:
        data = extractedData[ alg.name ]
        rC,gC,bC = alg.color
        C = (rC/255.0,gC/255.0,bC/255.0)
        
        lineWidthCurve = 10/3
        zorderCurve = 3

        line, = plt.plot(data[0], data[1] ,
                         label=alg.name, markevery=10, markersize=16,
                         linewidth=lineWidthCurve, color=C, linestyle=alg.curveStyle)
        line.set_zorder(zorderCurve)
    
        print("isLogLog = " + str(isLogLog))     
        if isLogLog:
            ax.set_xlim(minxvalue,xAxis[-1])
            lowerLimit = 0.1
            ax.set_ylim(0,maxyvalue+0.01)
            #ax.set_yscale('log')
            #ax.set_xscale('log')
            ax.loglog()
            ax.set_xticks(xAxis) # 1200

            # If a time label is requested
            if(opts.timelabel):
                ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
            ax.xaxis.set_tick_params(labelsize=sizeOfFont)
            ax.set_yticks(yAxis) # 
            ax.get_yaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
            ax.yaxis.set_tick_params(labelsize=sizeOfFont)
            ax.grid(color='black', linestyle='--', linewidth=2/3)
        else:
            print("No log is not implemented yet")
            ax.set_xlim(minxvalue,xAxis[-1])
            lowerLimit = 0
            if errorName == "rmse_time":
                lowerLimit = 0.02
            else:
                lowerLimit = 0.1
            ax.set_ylim(0,maxyvalue+0.01)
            #ax.set_yscale('log')
            #ax.set_xscale('log')
            #ax.loglog()
            ax.set_xticks(xAxis) # 1200

            # If a time label is requested
            if(opts.timelabel):
                ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
            ax.xaxis.set_tick_params(labelsize=sizeOfFont)
            ax.set_yticks([minyvalue,(minyvalue+maxyvalueFocus)*0.5,maxyvalue])
            ax.get_yaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
            ax.yaxis.set_tick_params(labelsize=sizeOfFont)
            ax.grid(color='black', linestyle='--', linewidth=2/3)
             
    
    # --- Setup order and style
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # --- Setup tick precision
    yy, locs = plt.yticks()
    ll = [ "{:.1E}".format(Decimal(str(a))) for a in yy]
    plt.yticks(yy, ll)
    
    # --- Setup tick space 
    for tick in ax.get_xaxis().get_major_ticks():
        tick.set_pad(8./3)
        #tick.set_fontproperties(ticks_font)
    for tick in ax.get_yaxis().get_major_ticks():
        tick.set_pad(16./3)
        #tick.set_fontproperties(ticks_font)
    
    # --- Remove minor tick up and right
    ax.tick_params(axis='x',which='minor',top='off')
    ax.tick_params(axis='y',which='minor',right='off')
    
    #if errorName == "rmse_time":
    #    plt.ylabel('RMSE',fontsize=40)
    #else:
    #  	plt.ylabel('NSD',fontsize=40)  
    #plt.xlabel('Time (sec.)',fontsize=40)  
    
    #if(isLogLog):
    #    plt.axes().set_aspect('equal')
        
    #legend = [a for a, b, c in algorithms]
    #plt.legend(legend, 'upper center', shadow=True, loc = 'upper right', bbox_to_anchor = (0.23, 0.23) )
    
    #plt.grid(True,lw=1,which='both')
    #plt.subplots_adjust(left=0.1, right=1, bottom=0.1, top=1.0)
    plt.savefig( opts.output, format='pdf' )
    #plt.savefig( dirName + os.path.sep + "plot_" + errorName + ".png", format='png' )
    #plt.show()
