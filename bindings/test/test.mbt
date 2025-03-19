///|
test "can_load_grammar" {
  let parser = @tree_sitter.Parser::new()
  let language = @tree_sitter_moonbit.language()
  parser.set_language(language)
}

///|
test "can_load_grammar" {
  let parser = @tree_sitter.Parser::new()
  let language = @tree_sitter_markdown_inline.language()
  parser.set_language(language)
}

///|
test "can_load_grammar" {
  let parser = @tree_sitter.Parser::new()
  let language = @tree_sitter_markdown.language()
  parser.set_language(language)
}

///|
test "can_load_grammar" {
  let parser = @tree_sitter.Parser::new()
  let language = @tree_sitter_yaml.language()
  parser.set_language(language)
}

///|
test "can_load_grammar" {
  let parser = @tree_sitter.Parser::new()
  let language = @tree_sitter_javascript.language()
  parser.set_language(language)
}

///|
test "can_load_grammar" {
  let parser = @tree_sitter.Parser::new()
  let language = @tree_sitter_json.language()
  parser.set_language(language)
}

///|
test "can_load_grammar" {
  let parser = @tree_sitter.Parser::new()
  let language = @tree_sitter_query.language()
  parser.set_language(language)
}

///|
test "can_load_grammar" {
  let parser = @tree_sitter.Parser::new()
  let language = @tree_sitter_c.language()
  parser.set_language(language)
}
