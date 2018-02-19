<?php


function get_help(){
	echo "usage: test.php [-h] [-r] [-p PATH] [-i PATH]\n
optional arguments:
  -h, --help\t\t\tshow this help message and exit
  -r, --recursive\t\tresursive tests search
  -p, --parse-script [PATH]\tname of parse script placed in this directory, default - parse.php
  -i, --int-script [PATH]\tname of interpreter script placed in this directory, default - interpret.py\n";
}

/* MAIN */
function main(){
	$shortopts  = "";
	$shortopts .= "h";
	$shortopts .= "r";
	$shortopts .= "p:";
	$shortopts .= "i:";
	$longopts = array(
		"help",
		"recursive",
		"parse-script:",
		"int-script:"
	);

	$options = getopt($shortopts, $longopts);
	if ($options === false){
		exit(10);
	}
	if (isset($options) && (isset($options['help']) || isset($options['h']))){
		get_help();
		exit(0);
	}

} 

main();
?>