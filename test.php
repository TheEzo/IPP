<?php

class TestCase{
	private $dir;
	private $recursive;
	private $parser;
	private $interpret;
	private $test_files = array();

	public function __construct($recursive, $dir, $parser, $interpret){
		if(!is_dir($dir)){
			// asi???
			exit(10);
		}
		if(!preg_match('/.+\/$/', $dir)){
			$dir = $dir.'/';
		}
		$this->dir = $dir;
		$this->recursive = $recursive;
		$this->parser = $parser;
		$this->interpret = $interpret;
		$this->get_files();
	}

	private function get_files(){
		if($this->recursive){
			$files = new RecursiveDirectoryIterator($this->dir);
			$files = new RecursiveIteratorIterator($files);
			foreach ($files as $file => $key) {
				if(preg_match('/^.+\\.(src|in|out|rc)$/', $file)){
					$this->test_files[] = $file;
				}
			}
			// var_dump($files);
		}
		else{
			$files = scandir($this->dir);
			foreach ($files as $file) {
				if(preg_match('/^.+\\.(src|in|out|rc)$/', $file)){
					$this->test_files[] = $this->dir.$file;
				}
			}
		}
		foreach ($this->test_files as $file) {
			if(preg_match('/^.+\\.src$/', $file)){
				$e = explode("/", $file);
				$p = array_pop($e);
				$p = explode('.', $p)[0];
				$path = implode('/', $e).'/';

				if(!$this->check($path, $p, '.in')){
					$this->create($path, $p, '.in');
				}
				if(!$this->check($path, $p, '.out')){
					$this->create($path, $p, '.out');
				}
				if(!$this->check($path, $p, '.rc')){
					$this->create($path, $p, '.rc');
				}
			}
		}

		// var_dump($this->test_files);
	}

	private function check($path, $name, $suffix){
		if(file_exists($path.$name.$suffix))
			return true;
		return false;
	}

	private function create($path, $name, $suffix){
		touch($path.$name.$suffix);
		if(!strcmp('.rc', $suffix)){
			$f = fopen($path.$name.$suffix, 'w');
			fwrite($f, '0');
			fclose($f);
		}
	}

	public function run_tests(){
		foreach ($this->test_files as $file) {
			if(!preg_match('/^.+\\.src$/', $file)){
				continue;
			}

			exec("php5.6 ".$this->parser." < ".$file." > output.tmp && python3.6 ".$this->interpret." --source output.tmp > output2.tmp", $output, $rc);

			$e = explode("/", $file);
			$p = array_pop($e);
			$name = explode('.', $p)[0];
			$path = implode('/', $e).'/';
			echo exec("diff output2.tmp ".$path.$name.".out")."\n";
		}
		exec('rm -f output2.tmp output.tmp');
	}


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
function main($argv){
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

	$options = getopt($shortopts, $longopts);
	if ($options === false){
		exit(10);
	}
	if (isset($options) && (isset($options['help']) || isset($options['h']))){
		get_help();
		exit(0);
	}
	if (count($argv) - 1 !== 0 && count($options) === 0){
		exit(10);
	}

	$parse_script = './parse.php';
	$int_script = './interpret.py';
	$dir = '.';
	$recursive = false;

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
	if(isset($options['r']) || isset($options['recursive']))
		$recursive = true;

	$t = new TestCase($recursive, $dir, $parse_script, $int_script);
	$t->run_tests();


} 

main($argv);
?>
