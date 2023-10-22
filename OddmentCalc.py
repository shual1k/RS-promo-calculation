import re

PROMO_RARITY = 3
PROMO_ODDS = 4
ODDMENTS_RARITY = 1
ODDMENTS_BASE = 5
ODDMENTS_CLAIM = 7
ROUND_ACCURACY_1 = 5
ROUND_ACCURACY_2 = 10
MAX_MULTIPLIER = 5

def fileContence(path):
    dataFile = open(path,"r")
    with dataFile:
        dataTable = dataFile.read()
    dataTable = dataTable.split("</tr>\n")
    return dataTable

def dictionatyFill(dict, key, val):
    if key not in dict:
        dict[key] = 0
    if (isinstance(val, float)):
        dict[key] += val
    else:
        dict[key] = val

def PercentToDecimal(dict):
    for key in dict:
        dict[key] = dict[key] / 100
        
def dictRound(dict, accuracy):
    for key in dict:
        dict[key] = round(dict[key],accuracy)

def dictProbFix(dict, accuracy):
    acc = 0
    for key in dict:
        acc += dict[key]
    ratioFix = 1/acc
    for key in dict:
        dict[key] = dict[key] * ratioFix
    dictRound(dict, accuracy)

def getKeys(dict):
    keys = list()
    for key in dict:
        keys.append(key)
    return keys

def rarityProb(path):
    newDict = dict()
    dataTable = fileContence(path)
    for dataEntry in dataTable:
        dataLines = dataEntry.split('\n')
        rarity = re.split(r"THGem-|.png", dataLines[PROMO_RARITY])[1] #<td style="text-align: center;"><img alt="THGem-very-rare.png"...
        chance = str(re.split(r">|%",dataLines[PROMO_ODDS])[1] )   #example: <td>2.18%
        chance = float(chance)
        dictionatyFill(newDict,rarity,chance)
    PercentToDecimal(newDict)
    dictRound(newDict, ROUND_ACCURACY_1)
    #dictProbFix(newDict, ROUND_ACCURACY_1)
    return newDict

def oddmentsPerRarity(path):
    newDict = dict()
    dataTable = fileContence("oddmentsPerRarity.txt")
    for dataEntry in dataTable:
        dataLines = dataEntry.split('\n')
        rarity = re.split(r"THGem-|.png", dataLines[ODDMENTS_RARITY])[1]
        baseOddments = int(dataLines[ODDMENTS_BASE][4:].replace(",",""))
        totalOddments = int(dataLines[ODDMENTS_CLAIM][4:].split(" ")[0].replace(",",""))
        claimOddments = totalOddments - baseOddments
        oddments = (baseOddments, claimOddments)
        dictionatyFill(newDict,rarity,oddments)
    return newDict

def multiplierProb(multipliersProb):
    newDict = dict()
    maxMul = len(multipliersProb)
    for mul in range(maxMul):
        dictionatyFill(newDict, mul + 1, multipliersProb[mul])
    return newDict

def CombineDicts(dict1, dict2):
    combinedDict = dict()
    for keyD1 in dict1:
        for keyD2 in dict2:
            newKey = str(keyD1) + " x" + str(keyD2)
            combinedDict[newKey] = dict1[keyD1] * dict2[keyD2]
    dictRound(combinedDict, ROUND_ACCURACY_2)
    return combinedDict

def OddmentsPerPrize(probDict, valueDict):
    newDict = dict()
    for probKey in probDict:
        probKeySplit = str(probKey).split(" x")
        rarity = str(probKeySplit[0])
        mul = int(probKeySplit[1])        
        base = int(valueDict[rarity][0])       
        claim = int(valueDict[rarity][1])
        newDict[probKey] = base + claim * mul
    return newDict

def sortDict(dictionary, sortedKeys):
    newDict = dict()
    for key in sortedKeys:
        newDict[key] = dictionary[key]
    return newDict
    
def cumulativeProbs(dictionary):
    newDict = dict()
    accumulator = 0
    for key in dictionary:
        accumulator += dictionary[key]
        newDict[key] = accumulator
    return newDict

"""
we have 3 boxes
for every possible result, assume result X is the best result:
probability of result X in box 1: P1 = P(box1=x) * P(box2<=x) * P(box3<=x)
probability of result X in box 2: P2 = P(box1<=x) * P(box2=x) * P(box3<=x)
probability of result X in box 3: P3 = P(box1<=x) * P(box2<=x) * P(box3=x)
probability of result X in all boxes: P4 = P(box1=x) * P(box2=x) * P(box3=x)
probability of getting X in any box:
P(res=X) = P1 + P2 + P3 - P4

sinse all boxes are the same:
    1. P(box1<=x) = P(box2<=x) = P(box3<=x) = pLEx
    2. P(box1=x) = P(box2=x) = P(box3=x) = pEQx
therefore: P1 = P2 = P3
therefore P(res=X) = 3 * pEQx * pLEx^2 - pEQx^3
"""
def bestOfThreeRollsProb(results, probDict, cumulProbDict):
    newDict = dict()
    for result in results:
        pEQres = probDict[result]
        PLEres = cumulProbDict[result]
        probRes = 3 * pEQres * PLEres**2 - pEQres**3
        newDict[result] = probRes
    return newDict

def oddmentsPerTry(results, probDict, oddmentDict):
    sum = 0
    for result in results:
        sum += probDict[result] * oddmentDict[result]
    return sum

def printDict(dict):
    for key in dict:
        s = str(key) + ": " + str(dict[key])
        print(s)

#initial dictionaries
rarityProbDict = rarityProb("foresightPromoProbabilities.txt")
oddmentsPerRarityDict = oddmentsPerRarity("oddmentsPerRarity.txt")
multiplierProbDict = multiplierProb([0.303, 0.379, 0.186, 0.066, 0.066])
#combines dictionaries
prizesProbDict = CombineDicts(rarityProbDict, multiplierProbDict)
oddmentsPerPrizeDict = OddmentsPerPrize(prizesProbDict, oddmentsPerRarityDict)
#sort dictionaries by oddment value
sortedKeys = sorted(oddmentsPerPrizeDict, key=oddmentsPerPrizeDict.get)
prizesProbDict = sortDict(prizesProbDict, sortedKeys)
oddmentsPerPrizeDict = sortDict(oddmentsPerPrizeDict, sortedKeys)
#calculate probabilities
cumulativePrizesProbDict = cumulativeProbs(prizesProbDict)
dictRound(cumulativePrizesProbDict, ROUND_ACCURACY_2)
pickBestOfThreeProb = bestOfThreeRollsProb(sortedKeys, prizesProbDict, cumulativePrizesProbDict)
oddments = oddmentsPerTry(sortedKeys, pickBestOfThreeProb, oddmentsPerPrizeDict)
print("expected oddments per key = ", oddments)