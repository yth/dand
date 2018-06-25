#!/usr/bin/python

import sys
import pickle
sys.path.append("../tools/")

from feature_format import featureFormat, targetFeatureSplit
from tester import dump_classifier_and_data

# My import
import numpy as np
# from pprint import pprint

### Task 1: Select what features you'll use.
### features_list is a list of strings, each of which is a feature name.
### The first feature must be "poi".

# Starting from an naive stand point, I might as well choose all the
# features to do my initial training, and then narrow down, transform,
# create other features depending on the result

# Do not include email_address as part of feature_list.
# It is not a numerical data type, and it might be a signature.

# Like a detective in a murder mystery, I will try to apply a deductive
# approached based on means, motive and opportunity.

# The obvious motive is for some monetary gain.
#
# Since we know the persons of interest might have perpetrated fraud,
# they probably will have multiple incomes sources from within the
# company. So, I will remove specific sources of potential gain, and
# look instead at the over all gain only (total_payment).
#
# Such a person might also be living beyond their means using the
# ill-gotten gain. I will leave "expenses" in as a feature.
#
# The nature of the fraud is such that Enron exes were artificially
# keeping the stock price up. As the result, I suspect each of them, or
# at least most of them will have a high stake in the stock price. I
# will keep "total_stock_value" as a feature, while remove all other
# stock related features.
#
# Means is harder to establish. The data does not give us the title of
# the various people under consideration. However, in order to pull off
# a scam of Enron's proportions, the perpetrators must have a means of
# communicating with each other.
#
# At the time of the Enron scandal, it was still in the relatively
# "early days" of the internet. People are probably less conscious of
# their email security. People might be emailing each other in a much
# more carefree manner. I would expect that there would be a large
# amount of mean both to and from poi. I will leave both
# "from_this_person_to_poi" and "from_poi_to_this_person" as features,
# I will remove to_messages and from_messages as features.
#
# Opportunity is harder to establish. I would expect most people
# involve in the scandal are in positions of power, or in key positions,
# without which, the scandal would have been unravelled earlier. This
# data set does not give us an easy way to get at this information.
# However, these people should have been well-rewarded, so I expect to
# a certain extent "total_payment" already captures some of this aspect
# of investigation.

features_list = ["poi",
				# "salary",
				# "to_messages", # new
				# "deferral_payments",
				"total_payments",
				# "exercised_stock_options",
				# "bonus",
				# "restricted_stock",
				"shared_receipt_with_poi",
				# "restricted_stock_deferred",
				"total_stock_value",
				"expenses",
				# "loan_advances",
				# "from_messages", # new
				# "other",
				# "from_this_person_to_poi", # newly removed
				# "director_fees",
				# "deferred_income",
				# "long_term_incentive",
				# "from_poi_to_this_person" # newly removed
]

### Load the dictionary containing the dataset
with open("final_project_dataset.pkl", "r") as data_file:
    data_dict = pickle.load(data_file)

# Get basic stats, especially POI Ratio (POI / Total Population)

print "Initial Population:",
print len(data_dict)

print "Total Features:",
print len(data_dict[data_dict.keys()[0]])

init_data = featureFormat(data_dict, features_list, sort_keys = True)
init_labels, init_features = targetFeatureSplit(init_data)
print "POI Number: ", sum(init_labels)
print "Init POI Ratio: " + str(sum(init_labels) / len(init_labels))


### Task 2: Deal with Outliers: Part 1
### Remove unuseful data

### Gather Data

n = 0 # Missing partial information
for key in data_dict.keys():
	for feature in data_dict[key].keys():
		if data_dict[key][feature] == "NaN":
			n += 1
			break

print "People with incomplete info: ", n

for key in data_dict.keys():
	for feature in features_list:
		if data_dict[key][feature] == "NaN":
			data_dict.pop(key)
			break

print "Stage 1 Population:", len(data_dict)

temp = featureFormat(data_dict, features_list, sort_keys = True)
temp_labels, temp_features = targetFeatureSplit(temp)
print "Part 1 POI Number: ", sum(temp_labels)
print "Part 1 POI Ratio: " + str(sum(temp_labels) / len(init_labels))

### Task 3: Create new feature(s)

# For new feature creation, I want to focus on communication.
# I will create two features, to and from email with POI as a % of total

feature1 = "to_poi_email_percentage"
feature2 = "from_poi_email_percentage"

for key in data_dict.keys():
	data_dict[key][feature1] = \
		float(data_dict[key]["from_this_person_to_poi"])/data_dict[key]["from_messages"]

	data_dict[key][feature2] = \
		float(data_dict[key]["from_poi_to_this_person"])/data_dict[key]["to_messages"]

features_list.append(feature1)
features_list.append(feature2)

# Stats

print "Final Population:", len(data_dict)

### Store to my_dataset for easy export below.

my_dataset = data_dict

# Change data_dict into usable form

data = featureFormat(data_dict, features_list, sort_keys = True)
labels, features = targetFeatureSplit(data)

### Task 2: Remove outliers: Part 2

# Remove the hardest to classify

from sklearn.linear_model import LinearRegression

reg = LinearRegression()
reg.fit(features, labels)
pred = reg.predict(features)

# Assuming that non-POI are more uniform, I will remove outliers from
# that population.
#
# It will both remove outlier, and increase my POI ratio.

N = len(labels)
TARGET = N * 0.5

while (len(labels) > TARGET):
	diff = (pred - labels) ** 2

	ordered_diff = sorted(diff, reverse=True)

	index = -1
	for i in ordered_diff:
		index = int(np.where(diff==i)[0])
		if labels[index] == 1:
			continue
		else:
			break

	if index != -1:
		pred = np.delete(pred, index)
		labels = np.delete(labels, index)
		features = np.delete(features, index, axis=0)

# I need to make sure that there are enough poi that remains. If there
# are none or too few, it would be too easy to guess that none of the
# people are poi.

print "POI Ratio: " + str(sum(labels) / len(labels))

print "Outlier remove stage 2 complete"

### Task 4: Try a varity of classifiers
### Please name your classifier clf for easy export below.
### Note that if you want to do PCA or other multi-stage operations,
### you'll need to use Pipelines. For more info:
### http://scikit-learn.org/stable/modules/pipeline.html

# I will be using a pipeline
from sklearn.pipeline import Pipeline

# First scale the data
from sklearn.preprocessing import MinMaxScaler

# Test naive assumption; maybe it will just work.
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier as DTC

estimators = [("scale", MinMaxScaler()),
			  ("classifier", DTC())]

clf = Pipeline(estimators)

### Task 5: Tune your classifier to achieve better than .3 precision and recall 
### using our testing script. Check the tester.py script in the final project
### folder for details on the evaluation method, especially the test_classifier
### function. Because of the small size of the dataset, the script uses
### stratified shuffle split cross validation. For more info: 
### http://scikit-learn.org/stable/modules/generated/sklearn.cross_validation.StratifiedShuffleSplit.html

# Algorithm Tuning

clf.set_params(classifier__criterion = "entropy")
clf.set_params(classifier__max_depth = 2)
# clf.set_params(classifier__min_samples_split = 2)

# Example starting point. Try investigating other evaluation techniques!
from sklearn.cross_validation import train_test_split
features_train, features_test, labels_train, labels_test = \
    train_test_split(features, labels, test_size=0.3, random_state=42)

# Naive approach, simply fit and test
clf.fit(features_train, labels_train)

pred = clf.predict(features)

from sklearn.metrics import accuracy_score, \
                            precision_score, \
                            recall_score, \
                            f1_score

print "Accuracy: " + str(accuracy_score(pred, labels))
print "Precision: " + str(precision_score(pred, labels))
print "Recall: " + str(recall_score(pred, labels))
print "f1: " + str(f1_score(pred, labels))

### Task 6: Dump your classifier, dataset, and features_list so anyone can
### check your results. You do not need to change anything below, but make sure
### that the version of poi_id.py that you submit can be run on its own and
### generates the necessary .pkl files for validating your results.

dump_classifier_and_data(clf, my_dataset, features_list)
