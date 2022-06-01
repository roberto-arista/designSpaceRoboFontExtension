import re
from fontTools import designspaceLib

from .parserTools import getLines, getBlocks, stringToNumber, numberToSTring


axisLabelRE = re.compile(r"[\"|\']([a-zA-Z0-9\- ]+)[\"|\']\s*([0-9\.]*)\s*([0-9\.]*)\s*([0-9\.]*)")
axisLabelLinkedUserValueRE = re.compile(r"\[([0-9\.]+)\]")
labelNameRE = re.compile(r"\?\s+([a-zA-Z\-]+)\s+[\"|\'](.*)[\"|\']")
userLocationRE = re.compile(r"([a-zA-Z\-\s]+)\s+([0-9\.]+)")

defaultLabelNameLanguageTag = "en"


def parseAxisLabels(text, axisLabelDescriptorClass=None):
    if axisLabelDescriptorClass is None:
        axisLabelDescriptorClass = designspaceLib.AxisLabelDescriptor
    labelNames = {}
    axisLabels = []
    currentAxisDescriptor = None
    for line in getLines(text):
        axisLabelfound = re.match(axisLabelRE, line)
        if axisLabelfound:
            labelName, minValue, value, maxValue = axisLabelfound.groups()
            if not minValue and not value and not maxValue:
                labelNames[defaultLabelNameLanguageTag] = labelName
            elif not value:
                minValue, value = value, minValue

            if value:
                lineLeftOver = line[axisLabelfound.end():]
                currentAxisDescriptor = axisLabelDescriptorClass(
                    name=labelName,
                    userValue=stringToNumber(value),
                    userMinimum=stringToNumber(minValue),
                    userMaximum=stringToNumber(maxValue),
                    elidable=bool("(elidable)" in lineLeftOver),
                    olderSibling=bool("(olderSibling)" in lineLeftOver)
                )
                axisLabels.append(currentAxisDescriptor)
                linkedUserValueFound = re.match(axisLabelLinkedUserValueRE, lineLeftOver)
                if linkedUserValueFound:
                    currentAxisDescriptor.linkedUserValue = float(linkedUserValueFound.groups()[0])

        else:
            labelNameFound = re.match(labelNameRE, line)
            if labelNameFound:
                languageTag, labelName = labelNameFound.groups()
                if currentAxisDescriptor is None:
                    labelNames[languageTag] = labelName
                else:
                    currentAxisDescriptor.labelNames[languageTag] = labelName

    return labelNames, axisLabels


def dumpAxisLabels(labelNames, axisLabels, indent="   "):
    text = []
    if defaultLabelNameLanguageTag in labelNames:
        text.append(f"'{labelNames[defaultLabelNameLanguageTag]}'")
    for languageTag, labelName in labelNames.items():
        if defaultLabelNameLanguageTag == languageTag:
            continue
        text.append(f"? {languageTag} '{labelName}'")

    if text:
        text.append("")
    for axisLabel in axisLabels:
        labelText = [f"'{axisLabel.name}'"]

        if axisLabel.userMinimum is not None:
            labelText.append(numberToSTring(axisLabel.userMinimum))
        labelText.append(numberToSTring(axisLabel.userValue))
        if axisLabel.userMaximum is not None:
            labelText.append(numberToSTring(axisLabel.userMaximum))

        if axisLabel.elidable:
            labelText.append("(elidable)")
        if axisLabel.olderSibling:
            labelText.append("(olderSibling)")
        if axisLabel.linkedUserValue:
            labelText.append(f"[{numberToSTring(axisLabel.linkedUserValue)}]")

        text.append(" ".join(labelText))

        for languageTag, labelName in axisLabel.labelNames.items():
            text.append(f"? {languageTag} '{labelName}'")
        text.append("")
    return "\n".join(text)


def parseLocationLabels(text, locationLabelDescriptorClass):
    locationLabels = []
    for labelName, lines in getBlocks(text).items():
        locationLabelDescriptor = locationLabelDescriptorClass(
            name=labelName,
            userLocation=dict(),
        )
        locationLabels.append(locationLabelDescriptor)

        for line in getLines(lines):
            labelNameFound = re.match(labelNameRE, line)
            if labelNameFound:
                languageTag, labelName = labelNameFound.groups()
                locationLabelDescriptor.labelNames[languageTag] = labelName

            userLocationFound = re.match(userLocationRE, line)
            if userLocationFound:
                axisName, value = userLocationFound.groups()
                locationLabelDescriptor.userLocation[axisName] = stringToNumber(value)
    return locationLabels


def dumpLocationLabels(locationLabels, indent="   "):
    text = []
    for locationLabel in locationLabels:
        text.append(locationLabel.name)
        for languageTag, labelName in locationLabel.labelNames.items():
            text.append(f"{indent}? {languageTag} \'{labelName}\'")
        text.append("")
        for axisName, value in locationLabel.userLocation.items():
            text.append(f"{indent}{axisName} {value}")
        text.append("")
    return "\n".join(text)


# axisLabelText = """
# "Weight"
# ? de "Extraleicht"

# # style name min value max
# "Extra Light" 200 200 250
# # optionally translations???
# ? de "Extraleicht"
# ? fr 'Extra léger'

# 'Light' 250 300 350
# 'Regular' 350 400 450 (elidable) (olderSibling)

# "Condensed" 50 [700]
# """


# locationLableText = """
# # style name (not a tag)
# A style
#     # optionally translation
#     ?  fr  "Un Style"
#     # location in user values
#     weight 300
#     width 40
#     Italic 1
#     boldness 30

# A other style
#     # optionally translation
#     ?  fr  "Un Style"
#     ? pr "bla bla"
#     # location in user values
#     weight 300
#     width 40
#     Italic 1
#     boldness 30
# """

# document = designspaceLib.DesignSpaceDocument()
# ln, al = parseAxisLabels(axisLabelText, document.writerClass.axisLabelDescriptorClass)
# #print(dumpAxisLabels(ln, al))


# l = parseLocationLabels(locationLableText, document.writerClass.locationLabelDescriptorClass)
# print(l)
# r = dumpLocationLabels(l)
# print(r)

