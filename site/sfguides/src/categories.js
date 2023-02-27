const fs = require('fs');
const path = require('path');

//object of {id:categories[]}
const newCategories = {}

const dirPath = '.';

function processFile(filePath) {
  const contents = fs.readFileSync(filePath, 'utf8');
  const lines = contents.split('\n');
  
  let id;
  let categoriesLine;
  
  for (const line of lines) {
    if (line.startsWith('id:')) {
      id = line.substring(3).trim();
    } else if (line.startsWith('categories:')) {
      categoriesLine = line;
    } else if (line.startsWith('##')) {
      break;
    }
  }
  
  if (id) {
    console.log(`Found ID ${id} in ${filePath}`);
  } else {
    console.log(`No ID found in ${filePath}`);
  }
  
  if (categoriesLine && id) {
    const newCategoriesLine = 'categories: ' + newCategories[id];
    const newContents = contents.replace(categoriesLine, newCategoriesLine);
    fs.writeFileSync(filePath, newContents);
    console.log(`Replaced categories line in ${filePath}`);
  } else {
    console.log(`No categories line found in ${filePath}`);
  }
}

function processDirectory(dirPath) {
  const files = fs.readdirSync(dirPath);
  
  for (const file of files) {
    const filePath = path.join(dirPath, file);
    const stats = fs.statSync(filePath);
    
    if (stats.isDirectory()) {
      processDirectory(filePath);
    } else if (stats.isFile() && path.extname(filePath) === '.md') {
      processFile(filePath);
    }
  }
}






processDirectory(dirPath);


