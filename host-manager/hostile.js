// Original code from https://github.com/feross/hostile
// Ported to deno by DPS0340 https://github.com/DPS0340
/*! hostile. MIT License. Feross Aboukhadijeh <https://feross.org/opensource> */
import fs from 'https://deno.land/std/node/fs.ts'
import process from 'https://deno.land/std/node/process.ts'
import once from 'https://cdn.skypack.dev/once'
import split from 'https://cdn.skypack.dev/split'
import string_decoder from 'https://cdn.skypack.dev/string_decoder'
import through from 'https://cdn.skypack.dev/through'

var WINDOWS = process.platform === 'win32'
var EOL = WINDOWS
  ? '\r\n'
  : '\n'

const HOSTS = WINDOWS
  ? 'C:/Windows/System32/drivers/etc/hosts'
  : '/etc/hosts'

export { HOSTS }

function isIp(ip) {  
  if (/^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/.test(ip)) {  
      return true 
  }  
  return false
}

/**
 * Get a list of the lines that make up the filePath. If the
 * `preserveFormatting` parameter is true, then include comments, blank lines
 * and other non-host entries in the result.
 *
 * @param  {boolean}   preserveFormatting
 * @param  {function(err, lines)=} cb
 */

export function getFile(filePath, preserveFormatting, cb) {
  var lines = []
  if (typeof cb !== 'function') {
    fs.readFileSync(filePath, { encoding: 'utf8' }).split(/\r?\n/).forEach(online)
    return lines
  }

  cb = once(cb)
  fs.createReadStream(filePath, { encoding: 'utf8' })
    .pipe(split())
    .pipe(through(online))
    .on('close', function () {
      cb(null, lines)
    })
    .on('error', cb)

  function online (line) {
    // Remove all comment text from the line
    var lineSansComments = line.replace(/#.*/, '')
    var matches = /^\s*?(.+?)\s+(.+?)\s*$/.exec(lineSansComments)
    if (matches && matches.length === 3) {
      // Found a hosts entry
      var ip = matches[1]
      var host = matches[2]
      lines.push([ip, host])
    } else {
      // Found a comment, blank line, or something else
      if (preserveFormatting) {
        lines.push(line)
      }
    }
  }
}

/**
 * Wrapper of `getFile` for getting a list of lines in the Host file
 *
 * @param  {boolean}   preserveFormatting
 * @param  {function(err, lines)=} cb
 */
export function get(preserveFormatting, cb) {
  return getFile(HOSTS, preserveFormatting, cb)
}

/**
 * Add a rule to /etc/hosts. If the rule already exists, then this does nothing.
 *
 * @param  {string}   ip
 * @param  {string}   host
 * @param  {function(Error)=} cb
 */
export function set(ip, host, cb) {
  var didUpdate = false
  if (typeof cb !== 'function') {
    return _set(get(true))
  }

  get(true, function (err, lines) {
    if (err) return cb(err)
    _set(lines)
  })

  function _set (lines) {
    // Try to update entry, if host already exists in file
    lines = lines.map(mapFunc)

    // If entry did not exist, let's add it
    if (!didUpdate) {
      // If the last line is empty, or just whitespace, then insert the new entry
      // right before it
      var lastLine = lines[lines.length - 1]
      if (typeof lastLine === 'string' && /\s*/.test(lastLine)) {
        lines.splice(lines.length - 1, 0, [ip, host])
      } else {
        lines.push([ip, host])
      }
    }

    writeFile(lines, cb)
  }

  function mapFunc (line) {
    // replace a line if both hostname and ip version of the address matches
    if (Array.isArray(line) && line[1] === host && isIp(line[0]) === isIp(ip)) {
      line[0] = ip
      didUpdate = true
    }
    return line
  }
}

/**
 * Remove a rule from /etc/hosts. If the rule does not exist, then this does
 * nothing.
 *
 * @param  {string}   ip
 * @param  {string}   host
 * @param  {function(Error)=} cb
 */
export function remove(ip, host, cb) {
  if (typeof cb !== 'function') {
    return _remove(get(true))
  }

  get(true, function (err, lines) {
    if (err) return cb(err)
    _remove(lines)
  })

  function _remove (lines) {
    // Try to remove entry, if it exists
    lines = lines.filter(filterFunc)
    return writeFile(lines, cb)
  }

  function filterFunc (line) {
    return !(Array.isArray(line) && line[0] === ip && line[1] === host)
  }
}

/**
 * Write out an array of lines to the host file. Assumes that they're in the
 * format that `get` returns.
 *
 * @param  {Array.<string|Array.<string>>} lines
 * @param  {function(Error)=} cb
 */
export function writeFile(lines, cb) {
  lines = lines.map(function (line, lineNum) {
    if (Array.isArray(line)) {
      line = line[0] + ' ' + line[1]
    }
    return line + (lineNum === lines.length - 1 ? '' : EOL)
  })

  if (typeof cb !== 'function') {
    var stat = fs.statSync(HOSTS)
    fs.writeFileSync(HOSTS, lines.join(''), { mode: stat.mode })
    return true
  }

  cb = once(cb)
  fs.stat(HOSTS, function (err, stat) {
    if (err) {
      return cb(err)
    }
    var s = fs.createWriteStream(HOSTS, { mode: stat.mode })
    s.on('close', cb)
    s.on('error', cb)

    lines.forEach(function (data) {
      s.write(data)
    })
    s.end()
  })
}