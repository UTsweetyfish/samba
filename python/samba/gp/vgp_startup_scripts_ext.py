# vgp_startup_scripts_ext samba gpo policy
# Copyright (C) David Mulder <dmulder@suse.com> 2021
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
from samba.gp.gpclass import gp_xml_ext, check_safe_path, gp_file_applier
from tempfile import NamedTemporaryFile
from samba.common import get_bytes
from subprocess import Popen, PIPE

intro = b'''
### autogenerated by samba
#
# This file is generated by the vgp_startup_scripts_ext Group Policy
# Client Side Extension. To modify the contents of this file,
# modify the appropriate Group Policy objects which apply
# to this machine. DO NOT MODIFY THIS FILE DIRECTLY.
#

'''

class vgp_startup_scripts_ext(gp_xml_ext, gp_file_applier):
    def __str__(self):
        return 'VGP/Unix Settings/Startup Scripts'

    def process_group_policy(self, deleted_gpo_list, changed_gpo_list,
                             cdir='/etc/cron.d'):
        for guid, settings in deleted_gpo_list:
            if str(self) in settings:
                for attribute, script in settings[str(self)].items():
                    self.unapply(guid, attribute, script)

        for gpo in changed_gpo_list:
            if gpo.file_sys_path:
                self.gp_db.set_guid(gpo.name)
                xml = 'MACHINE/VGP/VTLA/Unix/Scripts/Startup/manifest.xml'
                path = os.path.join(gpo.file_sys_path, xml)
                xml_conf = self.parse(path)
                if not xml_conf:
                    continue
                policy = xml_conf.find('policysetting')
                data = policy.find('data')
                attributes = []
                for listelement in data.findall('listelement'):
                    local_path = self.lp.cache_path('gpo_cache')
                    script = listelement.find('script').text
                    script_file = os.path.join(local_path,
                        os.path.dirname(check_safe_path(path)).upper(),
                                        script.upper())
                    parameters = listelement.find('parameters')
                    if parameters is not None:
                        parameters = parameters.text
                    else:
                        parameters = ''
                    value_hash = listelement.find('hash').text
                    attribute = self.generate_attribute(script_file,
                                                        parameters)
                    attributes.append(attribute)
                    run_as = listelement.find('run_as')
                    if run_as is not None:
                        run_as = run_as.text
                    else:
                        run_as = 'root'
                    run_once = listelement.find('run_once') is not None
                    if run_once:
                        def applier_func(script_file, parameters):
                            Popen(['/bin/sh %s %s' % (script_file, parameters)],
                                shell=True).wait()
                            # Run once scripts don't create a file to unapply,
                            # so their is nothing to return.
                            return []
                        self.apply(gpo.name, attribute, value_hash, applier_func,
                                   script_file, parameters)
                    else:
                        def applier_func(run_as, script_file, parameters):
                            entry = '@reboot %s %s %s' % (run_as, script_file,
                                                          parameters)
                            with NamedTemporaryFile(prefix='gp_', dir=cdir,
                                                    delete=False) as f:
                                f.write(intro)
                                f.write(get_bytes(entry))
                                os.chmod(f.name, 0o700)
                                return [f.name]
                        self.apply(gpo.name, attribute, value_hash, applier_func,
                                   run_as, script_file, parameters)

                    self.clean(gpo.name, keep=attributes)

    def rsop(self, gpo):
        output = {}
        xml = 'MACHINE/VGP/VTLA/Unix/Scripts/Startup/manifest.xml'
        if gpo.file_sys_path:
            path = os.path.join(gpo.file_sys_path, xml)
            xml_conf = self.parse(path)
            if not xml_conf:
                return output
            policy = xml_conf.find('policysetting')
            data = policy.find('data')
            for listelement in data.findall('listelement'):
                local_path = self.lp.cache_path('gpo_cache')
                script = listelement.find('script').text
                script_file = os.path.join(local_path,
                    os.path.dirname(check_safe_path(path)).upper(),
                                    script.upper())
                parameters = listelement.find('parameters')
                if parameters is not None:
                    parameters = parameters.text
                else:
                    parameters = ''
                run_as = listelement.find('run_as')
                if run_as is not None:
                    run_as = run_as.text
                else:
                    run_as = 'root'
                run_once = listelement.find('run_once') is not None
                if run_once:
                    entry = 'Run once as: %s `%s %s`' % (run_as, script_file,
                                                         parameters)
                else:
                    entry = '@reboot %s %s %s' % (run_as, script_file,
                                                  parameters)
                if str(self) not in output.keys():
                    output[str(self)] = []
                output[str(self)].append(entry)
        return output