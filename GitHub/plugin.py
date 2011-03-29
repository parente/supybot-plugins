###
# Copyright (c) 2011, Peter Parente
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###
import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import json

class GitHub(callbacks.Plugin):
    """Add the help for "@plugin help GitHub" here
    This should describe *how* to use this plugin."""
    threaded = True

    def issues(self, irc, msg, args, opts, label, repo, user):
        """[--{closed}] [<label>] [<repo>] [<user>] 

        Lists the issues for the http://github.com/user/repo repository with 
        the optional <label> in either the open (default) or --closed
        state. If <user> and <repo> are ommitted, the configured values for 
        these parameters are used.
        """
        user = user if user is not None else conf.supybot.plugins.GitHub.user
        repo = repo if repo is not None else conf.supybot.plugins.GitHub.repo
        label = label if label is not None else None
        opts = dict(opts)
        closed = opts.get('closed', False)
        state = 'closed' if closed else 'open'
        url = 'http://github.com/api/v2/json/issues/list/%s/%s' % (user, repo)
        if label:
            url += '/label/'+label
        else:
            url += '/' + state
        data = utils.web.getUrl(url)
        obj = json.loads(data)
        obj['issues'].sort(key=lambda i: i['position'])
        arr = [
            utils.str.format('%s %u', i['title'], i['html_url'])
            for i in obj['issues']
            if i['state'] == state
        ]
        if arr:
            irc.reply(utils.str.format('%L', arr))
        else:
            irc.reply('There are no matching issues.')
    issues = wrap(issues, [ 
        getopts({
            'closed':''
        }),
        optional('anything'), optional('anything'), optional('anything')
    ])

    def commits(self, irc, msg, args, branchOrHash, repo, user):
        '''[<branchOrHash>] [<repo>] [<user>]
        
        Lists the most recent commits on a branch or details about a single 
        commit identified by its hash. If <user> and <repo> are ommitted, the 
        configured values for these parameters are used.
        '''
        user = user if user is not None else conf.supybot.plugins.GitHub.user
        repo = repo if repo is not None else conf.supybot.plugins.GitHub.repo
        branchOrHash = branchOrHash if branchOrHash is not None else 'master'
        url = 'http://github.com/api/v2/json/commits/%s/%s/%s/%s'

        single = False
        try:
            # guess if we've got a hash
            single = len(branchOrHash) == 40 and int(branchOrHash, 16)
        except ValueError:
            # otherwise assume a branch
            pass
        
        if single:
            url = url % ('show', user, repo, branchOrHash)
            data = utils.web.getUrl(url)
            obj = json.loads(data)
            i = obj.get('commit')
            if i is not None:
                msg = utils.str.format('%s %u', i['message'], 'http://github.com'+i['url'])
                irc.reply(msg)
            else:
                irc.reply('There is no commit with hash %s.' % branchOrHash)
        else: 
            url = url % ('list', user, repo, branchOrHash)
            data = utils.web.getUrl(url)
            obj = json.loads(data)
            arr = [
                utils.str.format('%s %u', i['message'], 'http://github.com'+i['url'])
                for i in obj['commits']
            ]
            if arr:
                irc.reply(utils.str.format('%L', arr))
            else:
                irc.reply('There are no recent commits.')
    commits = wrap(commits, [
        optional('anything'),
        optional('anything'),
        optional('anything')
    ])
    
    def watchers(self, irc, msg, args, repo, user):
        '''[<repo>] [<user>]
        
        Gets the number of watchers for a given repository. If <user> and 
        <repo> are ommitted, the configured values for these parameters are 
        used.
        '''
        user = user if user is not None else conf.supybot.plugins.GitHub.user
        repo = repo if repo is not None else conf.supybot.plugins.GitHub.repo
        url = 'http://github.com/api/v2/json/repos/show/%s/%s/watchers' % (
            user, repo)
        data = utils.web.getUrl(url)
        obj = json.loads(data)
        count = len(obj['watchers'])
        irc.reply('There are %d people watching %s/%s' % (count, user, repo))
    watchers = wrap(watchers, [
        optional('anything'),
        optional('anything')
    ])
    
    def tags(self, irc, msg, args, repo, user):
        '''[<repo>] [<user>]
        
        Gets the tags in a given repository. If <user> and <repo> are ommitted,
        the configured values for these parameters are used.
        '''
        user = user if user is not None else conf.supybot.plugins.GitHub.user
        repo = repo if repo is not None else conf.supybot.plugins.GitHub.repo
        url = 'http://github.com/api/v2/json/repos/show/%s/%s/tags' % (
            user, repo)
        data = utils.web.getUrl(url)
        obj = json.loads(data)
        tags = obj.get('tags')
        if tags:
            irc.reply(utils.str.format('%L', tags.keys()))
        else:
            irc.reply('There are no tags in %s/%s' % (user, repo))
    tags = wrap(tags, [
        optional('anything'),
        optional('anything')
    ])
    
    def branches(self, irc, msg, args, repo, user):
        '''[<repo>] [<user>]
        
        Gets the branches in a given repository. If <user> and <repo> are 
        ommitted, the configured values for these parameters are used.
        '''
        user = user if user is not None else conf.supybot.plugins.GitHub.user
        repo = repo if repo is not None else conf.supybot.plugins.GitHub.repo
        url = 'http://github.com/api/v2/json/repos/show/%s/%s/branches' % (
            user, repo)
        data = utils.web.getUrl(url)
        obj = json.loads(data)
        branches = obj.get('branches')
        if branches:
            irc.reply(utils.str.format('%L', branches.keys()))
        else:
            irc.reply('There are no branches in %s/%s' % (user, repo))
    branches = wrap(branches, [
        optional('anything'),
        optional('anything')
    ])

Class = GitHub

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
