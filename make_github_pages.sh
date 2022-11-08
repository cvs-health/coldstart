#rename docs to html
mv docs html

#change directory to html
cd html

#make documents
make html

#create .nojekyll file
touch .nojekyll

#change directory back to root dir
cd ..

#rename html to docs
mv html docs