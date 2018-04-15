<?php

/* třída pro vytvoření html kódu */
class HTMLGenerator{
	private $fails = 0;
	private $success = 0;
	private $body = "";

	/* vygeneruje html kostru */
	public function get_html(){
		$skelet =  "
<!DOCTYPE html>
<html>
<head>
<title>IPP tests results</title>
<style>
.red {
	color: red;
}
.green{
	color: green;
}
.text-center{
	text-align: center;
}
body{
	margin: 0 auto;
	width: 1000px;
	align: center;
}
.w-20{
	width: 20%;
}
.w-10{
	width: 10%;
}
.w-70{
	width: 70%;
}
</style>
</head>
<body>
	<div>
		<div class=\"\">
			<center>
				<h1>IPP tests results</h1>
				<span>".($this->fails+$this->success)." tests total</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
				<span class=\"red\">".$this->fails." failed</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
				<span class=\"green\">".$this->success." passed</span>
			</center>
			<br><br><br>
		</div>
		<table border=\"1\">
		<tr>
			<th class=\"w-20\">Test</th>
			<th class=\"w-70\">Diff result<br>real output [difference sign] expected output</th>
			<th class=\"w-10\">Return code<br>expected:got</th>
		</tr>".$this->body."</table>
	</div>
</body>
</html>\n";
		echo $skelet;
	}

	/* inkrementuje patřičné čísla a přidá html kód s výsledkem testu */
	public function add_test($test, $diff, $rc, $expected_rc, $passed){
		$passed ? $this->success++ : $this->fails++;
		$this->body = $this->body."
<tr>
	<td class=\"text-center ".($passed ? "green" : "red")."\">".$test."</td>
	<td class=\"text-center\">".$diff."</td>
	<td class=\"text-center\">".$expected_rc.":".$rc."</td>
</tr>";
	}

}

/* třída pro nalezení a spuštění testů */
class TestCase{
	private $dir;
	private $recursive;
	private $parser;
	private $interpret;
	private $test_files = array();
	private $child = 0;

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

	/* projde rekurzivně nebo nerekurzivně zadaný adresář a najde všechny testy */
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
	}

	/* kontroluje, jestli soubor path/name.suffix existuje */
	private function check($path, $name, $suffix){
		if(file_exists($path.$name.$suffix))
			return true;
		return false;
	}

	/* vytvoří soubor path/name.suffix */
	private function create($path, $name, $suffix){
		touch($path.$name.$suffix);
		if(!strcmp('.rc', $suffix)){
			$f = fopen($path.$name.$suffix, 'w');
			fwrite($f, '0');
			fclose($f);
		}
	}

	/* pro každý detekovaný zdrojový soubor spustí test a zavolá metodu pro generování html výsledku testu */ 
	public function run_tests(){
		$h = new HTMLGenerator();
		foreach ($this->test_files as $file) {
			touch('/tmp/output2.tmp');
			touch('/tmp/output.tmp');
			if(!preg_match('/^.+\\.src$/', $file)){
				continue;
			}
			$passed = true;
			$e = explode("/", $file);
			$p = array_pop($e);
			$name = explode('.', $p)[0];
			$path = implode('/', $e).'/';
			exec("timeout 20 php5.6 ".$this->parser." < ".
			$file." > /tmp/output.tmp", $output, $rc);
			if($rc === 0){
				exec('cat "'.$path.$name.'".in | timeout 20 python3.6 '.$this->interpret.
				" --source /tmp/output.tmp > /tmp/output2.tmp", $output, $rc);
			}
			if((int)$rc === 124){
				$h->add_test($path.$name, "<span style=\"color: red;\">TEST TIMEOUTED!</span>", 0, 0, false);
			}
			else{
				if($rc !== 21)
					$out = exec('diff /tmp/output2.tmp "'.$path.$name.'".out');
				else
					$out = '';
				$passed = true;
				if(strlen($out) > 1){
					$passed = false;
				}
				$f = fopen($path.$name.".rc", "r");
				$expected_rc = fread($f, filesize($path.$name.".rc"));
				if((int)$expected_rc !== $rc)
					$passed = false;			
				fclose($f);
				if($out !== ''){
					exec('diff -y /tmp/output2.tmp "'.$path.$name.'".out', $out);
					$out = implode("<br>", $out);
				}
				$h->add_test($path.$name, $out, $rc, $expected_rc, $passed);
			}
		}
		exec('rm -f /tmp/output2.tmp /tmp/output.tmp');
		$h->get_html();
	}


}


function get_help(){
	echo "usage: test.php [-h] [-r] [-p PATH] [-i PATH]\n
optional arguments:
  -h, --help\t\t\tshow this help message and exit
  -r, --recursive\t\tresursive tests search
  -d, --directory PATH\tdirectory which contains test files (*.src, *.in, *.out, *.rc), default - '.'
  -p, --parse-script PATH\tname of parse script placed in this directory, default - parse.php
  -i, --int-script PATH\tname of interpreter script placed in this directory, default - interpret.py\n\n
  Each test have 20 sec timeout in interpret or in parser\n";
}

/* MAIN */
/* zkontroluje argumenty a spustí testy */
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
