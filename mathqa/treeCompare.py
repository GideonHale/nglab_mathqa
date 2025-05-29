import copy
import xml.etree.ElementTree as ET
from collections import deque

def compareTrees(Lfile, Rfile) -> float:
  """
  Compare two MathML trees and return a score based on their structure and branching nodes.
  The score is calculated based on the depth and complexity of the trees by way of scoreTree().
  
  Parameters:
    Lfile (str): Path to the first XML file.
    Rfile (str): Path to the second XML file.
  Returns:
    float: A score representing the similarity between the two trees.
  """
  Ltree = ET.parse(Lfile)
  Rtree = ET.parse(Rfile)
  LpathsArr = parseTree(Ltree)
  RpathsArr = parseTree(Rtree)
  score: float = scoreTree(LpathsArr, RpathsArr)
  return score

def parseTree(tree: ET.ElementTree):
  """
  Sketches out an XML file (in our case specifically MathML) in a tree structure.
  Only holds on to tags and drops the actual values contained in them.

  Parameters:
    tree (ET.ElementTree): the MathML file encoded into tree format
  Returns:
    array: the tree sketch representation of the XML file
  """
  root = tree.getroot()
  childNodes = deque()
  childNodes.append([root, []])
  curPath: list = []
  pathsArr: list = []
  
  while True:
    if len(childNodes) == 0:
      break
    
    curNode, curPath = copy.deepcopy(childNodes.pop())
    curPath.append(curNode)
    if len(list(curNode)) == 0: # No children
      pathsArr.append(curPath)
      continue
    
    fork = 0
    for child in curNode:
      if isBranchNode(curNode):
        curPath.append(fork)
        fork += 1
        childNodes.append((child, curPath.copy()))
        curPath.pop()
      else:
        childNodes.append((child, curPath.copy()))

  pathsArr = convertPathToString(pathsArr)
  return pathsArr

# these are common MathML tags that we've decided have a significant effect on the formula
BRANCHING_NODES = [
  "mover",
  "munder",
  "munderover",
  "mfrac",
  "msup",
  "msubsup",
  "msqrt"
]        

def isBranchNode(node):
  strNode = str(node)
  isBranchingNode = False
  for branchingNode in BRANCHING_NODES:
    if branchingNode in strNode:
      isBranchingNode = True
      break
  return(not isinstance(node, int) and isBranchingNode)

def convertPathToString(pathsArr):
  pathsArrStr = []
  for path in pathsArr:
    pathsStr = []
    for node in path:
      if isinstance(node, int):
        tag = node
        pathsStr.append(tag)
      else:
        tag = node.tag.split("}")[-1]
        if "mstyle" not in tag:
          pathsStr.append(tag)
    pathsArrStr.append(pathsStr)
  return pathsArrStr

def scoreTree(LpathsArr, RpathsArr) -> float:
  branchScoresArr = []
  for Rpath in RpathsArr:
    bestBranchScore = 0
    matchingWeight = 1 # Might not even be necessary but clean
    for Lpath in LpathsArr:
      branchScore, weight = getBranchInfo(Lpath, Rpath)
      if branchScore > bestBranchScore:
        bestBranchScore = branchScore
        matchingWeight = weight
    branchScoresArr.append(bestBranchScore * matchingWeight)
    
  depthScore = sum(branchScoresArr) / len(branchScoresArr)
  Lsize = sum(len(path) for path in LpathsArr)
  Rsize = sum(len(path) for path in RpathsArr)
  minSize = min(Lsize, Rsize)
  maxSize = max(Lsize, Rsize)
  complexityScore = minSize / maxSize
  
  # Weight is "hardcoded" here
  depthWeight = 1 - depthScore
  complexityWeight = depthScore
  return complexityScore * complexityWeight + depthScore * depthWeight

def getBranchInfo(Lpath, Rpath):
  bestDepth = longestContigSubseqCount(Lpath[1:], Rpath[1:]) # Skip math
  score = bestDepth/(len(Rpath) - 1) # -1 to account for math, present in every branch.
  LbranchingCounts, RbranchingCounts = countBranching(Lpath, Rpath) 
  weight = getWeight(LbranchingCounts, RbranchingCounts)  
  return score, weight

def longestContigSubseqCount(Lpath, Rpath):
  m, n = len(Lpath), len(Rpath)
  table = [[0] * (n + 1) for _ in range(m + 1)] # Create and fill with 0
  bestDepth = 0

  for i in range(1, m + 1):
    for j in range(1, n + 1):
      if Lpath[i - 1] == Rpath[j - 1]:
        table[i][j] = table[i - 1][j - 1] + 1
        bestDepth = max(bestDepth, table[i][j])
      else:
        table[i][j] = 0
  return bestDepth

def countBranching(Lpath, Rpath):
  LbranchingCounts = {}
  RbranchingCounts = {}
  # Need to be specific because <mo> is in <mover>
  for branchingNode in BRANCHING_NODES:
    for Lnode in Lpath:
      if isinstance(Lnode, int):
        continue
      if Lnode == branchingNode:
        LbranchingCounts[branchingNode] = LbranchingCounts.get(branchingNode, 0) + 1
    for Rnode in Rpath:
      if isinstance(Rnode, int):
        continue
      if Rnode == branchingNode:
        RbranchingCounts[branchingNode] = RbranchingCounts.get(branchingNode, 0) + 1
  return LbranchingCounts, RbranchingCounts

MOVER_WEIGHT = 0.005
MUNDER_WEIGHT = 0.005
MUNDEROVER_WEIGHT = 0.005
MFRAC_WEIGHT = 0.5
MSUP_WEIGHT = 0.5
MSUBSUP_WEIGHT = 0.5
MSQRT_WEIGHT = 0.5
def getWeight(LbranchingNodes, RbranchingNodes):
  keys = BRANCHING_NODES.copy()
  keyToWeight = {
    "mover": MOVER_WEIGHT,
    "munder": MUNDER_WEIGHT,
    "munderover": MUNDEROVER_WEIGHT,
    "mfrac": MFRAC_WEIGHT,
    "msup": MSUP_WEIGHT,
    "msubsup": MSUBSUP_WEIGHT,
    "msqrt": MSQRT_WEIGHT
    }
  
  weight = 1
  for key in keys:
    difference = abs(LbranchingNodes.get(key, 0) - RbranchingNodes.get(key, 0))
    weight = weight * (keyToWeight[key] ** difference)
  return weight

# Testing stuff
def printTree(tree):
  root = tree.getroot()
  for node in root.iter():
    # Check if the node has no children (leaf node)
    if len(list(node)) == 0 and node.text and node.text.strip():
      # Only print if the node has text (non-empty, non-whitespace)
      tag = node.tag.split("}")[-1]
      print(tag, "=", node.text.strip())  # Print the tag and text content
  return None
