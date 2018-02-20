<?php

class XML extends XMLWriter{
	// třída XML obsahuje metody pro tvorbu xml výstupu

	public $counter = 0;

	function __construct(){
		$this->openMemory();
		$this->setIndent(true);
		$this->startDocument('1.0', 'UTF-8'); 
		$this->startElement('program');
		$this->writeAttribute('language', 'IPPcode18');
	}

	public function add_instruction($opcode, $arg1=false, $arg1_type=false, $arg2=false, $arg2_type=false, $arg3=false, $arg3_type=false){
		$this->startElement('instruction');
		$this->writeAttribute('order', ++$this->counter);
		$this->writeAttribute('opcode', $opcode);
		if ($arg1_type){
			$this->add_element('arg1', $arg1, $arg1_type);
		}
		if ($arg2_type){
			$this->add_element('arg2', $arg2, $arg2_type);
		}
		if ($arg3_type){
			$this->add_element('arg3', $arg3, $arg3_type);
		}
		$this->endElement();
	}

	private function add_element($arg, $text, $type){
		$this->startElement($arg);
		$this->writeAttribute('type', $type);
		$this->text($text);
		$this->endElement();
	}
	
	private function get_document(){ 

        $this->endElement(); 
        $this->endDocument(); 
        return $this->outputMemory(); 
    } 

    public function output(){ 
        echo $this->get_document(); 
    } 
}


class Parse{
	// třída Parse načte data ze standartního vstupu a pomocí třídy XML je zpracuje

	private function read_stdin(){
		while($line = fgets(STDIN)){
			yield $line;
		}
	}

	public function get_word(){
		$skip = false;
		$first_line = true;
		foreach ($this->read_stdin() as $line){
			$l = $this->split_command($line);
			if ($l === false)
				continue;
			for($i = 0; $i < count($l); $i++){
				$e = explode("\n", $l[$i]);
				if(count($e) > 1){
					$l[$i] = $e[0];
				}
				if(strcmp(substr($l[$i], 0, 1), "#") === 0){
					$skip = true;
					continue;
				}
				if($first_line && !$skip){
					$first_line = false;
					$skip = true;
					$e = explode("\n", $l[$i]);
					if(!strcmp(".IPPcode18", $e[0]))
						continue;
					else
						exit(21);
				}
				if(!$skip){
					yield $l[$i];
				}

			}
			if($skip)
				$skip = false;
			else
				yield -1;
		}
	}

	public function split($i){
		$s = preg_split("/[\n@]/", $i);
		for($j = 0; $j < count($s); $j++){
			if(strlen($s[$j]) === 0)
				unset($s[$j]);
		}
		return $s;
	}

	private function split_command($c){
		if (preg_match('/^\s*#.*$/', $c))
			return false;
		$comment = false;
		$l = preg_split("/[\t ]/", $c);
		if (count($l) === 1){
			if ($l[0] === "\n"){
				return false;
			}
		}
		// odstraní prázdné prvky nebo komentáře
		for($i = 0; $i < count($l); $i++){
			$x = explode("#", $l[$i]);
			if(!strcmp("\n", $l[$i])){
				unset($l[$i]);
			}
			elseif (count($x) !== 1){
				$comment = true;
				$l[$i] = $x[0];
				$l = array_slice($l, 0, $i+1);
			}
			elseif(strlen($l[$i]) === 0){
				unset($l[$i]);
				$l = array_values($l);
				$i = -1;
			}
		}
		return $l;
	}

	public function is_var($i){
		if(!isset($i[1])){
			return false;
		}
		if(preg_match('/^(GF|LF|TF)@(-|_|\$|\*|%|&|\w)[\w\d-_\$\*%&]*$/u', $i[0]."@".$i[1]))
			return true;
		return false;
	}

	public function is_const($i){
		$string = $i[0]."@".(isset($i[1]) ? $i[1] : '');
		if(!isset($i[1])){
			if(preg_match('/^string@(\\\0([0-2]\d|3[0-2])|(?!(\\\|#))[[:print:]])*$/u', $string)) {
				return true;
			}
			else
				return false;
		}
		echo $string."\n";
		if(preg_match('/^string@(\\\0([0-2]\d|3[0-2]|35|92)|(?!(\\\|#))[\x{0021}-\x{FFFF}])*$/u', $string)){	
			return true;
		}
		echo $string."\n";
		if(preg_match('/^bool@(true|false)$/u', $i[0]."@".$i[1]))
			return true;
		if(preg_match('/^int@((-|\+)?[1-9]\d*|0)$/u', $i[0]."@".$i[1])) 
			return true;
		return false;
	}

	public function is_type($i){
		if(preg_match('/^(int|bool|string)$/u', $i)){
			return true;
		}
		return false;
	}

	public function is_label($i){
		if(preg_match('/^(-|_|\$|\*|%|&|\w)[\w\d-_\$\*%&]*$/u', $i))
			return true;
		return false;
	}
}


class Variables{
	public $counter;
	public $instruct;
	public $arg1;
	public $arg1_type;
	public $arg2;
	public $arg2_type;
	public $arg3;
	public $arg3_type;

	public function reinit(){
		$this->counter = 0;
		$this->instruct = '';
		$this->arg1 = false;
		$this->arg1_type = false;
		$this->arg2 = false;
		$this->arg2_type = false;
		$this->arg3 = false;
		$this->arg3_type = false;
	}
}

function get_help(){
	echo "usage: parse.php [-h]\n
optional arguments:
  -h, --help\t\tshow this help message and exit\n";
}

/* MAIN */
function main(){
	$shortopts  = "";
	$shortopts .= "h";
	$longopts = array(
		"help",
	);

	$options = getopt($shortopts, $longopts);
	if ($options === false){
		exit(10);
	}
	if (isset($options) && (isset($options['help']) || isset($options['h']))){
		get_help();
		exit(0);
	}



	$instructions = array(
		"MOVE" => array('var', 'symb'),
		"CREATEFRAME" => array(),
		"PUSHFRAME" => array(),
		"POPFRAME" => array(),
		"DEFVAR" => array('var'),
		"CALL" => array('label'),
		"RETURN" => array(),

		"PUSHS" => array('symb'),
		"POPS" => array('var'),
		
		"ADD" => array('var', 'symb', 'symb'),
		"SUB" => array('var', 'symb', 'symb'),
		"MUL" => array('var', 'symb', 'symb'),
		"IDIV" => array('var', 'symb', 'symb'),
		"LT" => array('var', 'symb', 'symb'),
		"GT" => array('var', 'symb', 'symb'),
		"EQ" => array('var', 'symb', 'symb'),
		"AND" => array('var', 'symb', 'symb'),
		"OR" => array('var', 'symb', 'symb'),
		"NOT" => array('var', 'symb', 'symb'),
		"INT2CHAR" => array('var', 'symb'),
		"STRI2INT" => array('var', 'symb', 'symb'),
		
		"READ" => array('var', 'type'),
		"WRITE" => array('symb'),
		
		"CONCAT" => array('var', 'symb', 'symb'),
		"STRLEN" => array('var', 'symb'),
		"GETCHAR" => array('var', 'symb', 'symb'),
		"SETCHAR" => array('var', 'symb', 'symb'),
		
		"TYPE" => array('var', 'symb'),
		
		"LABEL" => array('label'),
		"JUMP" => array('label'),
		"JUMPIFEQ" => array('label', 'symb', 'symb'),
		"JUMPIFNEQ" => array('label', 'symb', 'symb'),
		
		"DPRINT" => array('symb'),
		"BREAK" => array(),
	);

	$x = new XML();
	$p = new Parse();
	$v = new Variables();
	$v->reinit();
	$data=array();

	foreach ($p->get_word() as $word) {
		if ($word === -1){
			if($v->counter-1 !== count($instructions[$v->instruct])){
				exit(21);
			}
			if($v->counter > 0){
				$x->add_instruction($v->instruct, $v->arg1, $v->arg1_type, $v->arg2, $v->arg2_type, $v->arg3, $v->arg3_type);
				$v->reinit();
			}
		}
		else{
			switch($v->counter){
				case 0:
					$v->instruct = strtoupper($word);
					if(!isset($instructions[$v->instruct])){
						exit(21);
					}
					else
						$data = $instructions[$v->instruct];
					break;
				case 1:
					if($v->counter > count($data))
						exit(21);
					$e = $p->split($word);
					if(strpos($word, "@") !== false){
						if(!strcmp($data[$v->counter-1], "symb")){
							if($p->is_var($e)){
								$v->arg1_type = "var";
								$v->arg1 = $e[0]."@".$e[1];
							}
							elseif($p->is_const($e)){
								$v->arg1_type = $e[0];
								$v->arg1 = (isset($e[1]) ? $e[1] : '');
							}
							else
								exit(21);
						}
						elseif(!strcmp($data[$v->counter-1], "var")){
							if($p->is_var($e)){
								$v->arg1_type = "var";
								$v->arg1 = $e[0]."@".$e[1];
							}
							else
								exit(21);
						}
						else
							exit(21);
					}
					else{
						if(!strcmp($data[$v->counter-1], "type")){
							if($p->is_type($e[0])){
								$v->arg1_type = "type";
								$v->arg1 = $e[0];
							}
						}
						elseif($p->is_label($e[0])){
							$v->arg1_type = "label";
							$v->arg1 = $e[0];
							if(isset($data[$v->counter-1]))
								if(strcmp($data[$v->counter-1], $v->arg1_type) !== 0)
									exit(21);
						}
						else{
							exit(21);
						}
					}
					break;
				case 2:
					if($v->counter > count($data))
						exit(21);
					$e = $p->split($word);
					if(strpos($word, "@") !== false){
						if(!strcmp($data[$v->counter-1], "symb")){
							if($p->is_var($e)){
								$v->arg2_type = "var";
								$v->arg2 = $e[0]."@".$e[1];
							}
							elseif($p->is_const($e)){
								$v->arg2_type = $e[0];
								$v->arg2 = (isset($e[1]) ? $e[1] : "");
							}
							else{
								exit(21);
							}
						}
						elseif(!strcmp($data[$v->counter-1], "var")){
							if($p->is_var($e)){
								$v->arg2_type = "var";
								$v->arg2 = $e[0]."@".$e[1];
							}
							else
								exit(21);
						}
						else
							exit(21);
					}
					else{
						if(!strcmp($data[$v->counter-1], "type")){
							if($p->is_type($e[0])){
								$v->arg2_type = "type";
								$v->arg2 = $e[0];
							}
						}
						elseif($p->is_label($e[0])){
							$v->arg2_type = "label";
							$v->arg2 = $e[0];
							if(isset($data[$v->counter-1]))
								if(strcmp($data[$v->counter-1], $v->arg2_type) !== 0)
									exit(21);
						}
						else{
							exit(21);
						}
					}
					break;
				case 3:
					if($v->counter > count($data))
						exit(21);
					$e = $p->split($word);
					if(strpos($word, "@") !== false){
						if(!strcmp($data[$v->counter-1], "symb")){
							if($p->is_var($e)){
								$v->arg3_type = "var";
								$v->arg3 = $e[0]."@".$e[1];
							}
							elseif($p->is_const($e)){
								$v->arg3_type = $e[0];
								$v->arg3 = (isset($e[1]) ? $e[1] : '');
							}
							else
								exit(21);
						}
						elseif(!strcmp($data[$v->counter-1], "var")){
							if($p->is_var($e)){
								$v->arg3_type = "var";
								$v->arg3 = $e[0]."@".$e[1];
							}
							else
								exit(21);
						}
						else
							exit(21);
					}
					else{
						if(!strcmp($data[$v->counter-1], "type")){
							if($p->is_type($e[0])){
								$v->arg3_type = "type";
								$v->arg3 = $e[0];
							}
						}
						elseif($p->is_label($e[0])){
							$v->arg3_type = "label";
							$v->arg3 = $e[0];
							if(isset($data[$v->counter-1]))
								if(strcmp($data[$v->counter-1], $v->arg3_type) !== 0)
									exit(21);
						}
						else{
							exit(21);
						}
					}
					break;
				default:
					return 21;
			}
			$v->counter++;
		}
	}

	$x->output();
	exit(0);
}
main();
?>