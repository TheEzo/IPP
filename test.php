<?php

class TestCase{

}


function get_help(){
	echo "usage: test.php [-h] [-r] [-p PATH] [-i PATH]\n
optional arguments:
  -h, --help\t\t\tshow this help message and exit
  -r, --recursive\t\tresursive tests search
  -d, --directory PATH\tdirectory which contains test files (*.src, *.in, *.out, *.rc), default - '.'
  -p, --parse-script PATH\tname of parse script placed in this directory, default - parse.php
  -i, --int-script PATH\tname of interpreter script placed in this directory, default - interpret.py\n";
}

/* MAIN */
function main(){
	$shortopts  = "";
	$shortopts .= "h";
	$shortopts .= "d:";
	$shortopts .= "r";
	$shortopts .= "p:";
	$shortopts .= "i:";
	$longopts = array(
		"help",
		"directory:",
		"recursive",
		"parse-script:",
		"int-script:"
	);

	// $execute = `php5.6 ./parse.php < ./tests/good/test1.src`;
	echo $execute;
	$options = getopt($shortopts, $longopts);
	if ($options === false){
		exit(10);
	}
	if (isset($options) && (isset($options['help']) || isset($options['h']))){
		get_help();
		exit(0);
	}


	$parse_script = 'parse.php';
	$int_script = 'interpret.py';
	$dir = '.';

	if(isset($options['p']))
		$parse_script = $options['p'];
	elseif(isset($options['parse-script']))
		$parse_script = $options['parse-script'];
	if(isset($options['i']))
		$int_script = $options['i'];
	elseif(isset($options['int-script']))
		$int_script = $options['int-script'];
	if(isset($options['d']))
		$dir = $options['d'];
	elseif(isset($options['directory']))
		$dir = $options['directory'];
	// var_dump($options);

	// scan and remove . and ..
	$files = array_slice(scandir($dir), 2);


	var_dump($files);
} 

main();
?>
