
from enum import IntFlag
from typing import Any

from sphinx.application import Sphinx
from sphinx.ext.autodoc import Documenter, ClassDocumenter, bool_option, ALL


class IntFlagDocumenter(ClassDocumenter):
    """ClassDocumenter subclass specifically for IntFlag classes. 
       Gives the option to document members as hex, with '0' fill.

       Enum values must be documented for this class to have
       an effect.

       Note this class is a hybrid of the sphinx IntEnum example and
       modified sphinx.ext.autodoc.__init__ source:

       https://www.sphinx-doc.org/en/master/development/tutorials/autodoc_ext.html
       https://github.com/sphinx-doc/sphinx/blob/4.5.x/sphinx/ext/autodoc/__init__.py#L890-L891
    """
    objtype = 'intflag'
    directivetype = ClassDocumenter.objtype
    priority = 0
    option_spec = dict(ClassDocumenter.option_spec)
    option_spec["hex"] = bool_option
    option_spec["fill"] = int

    @classmethod
    def can_document_member(cls, 
                            member: Any,
                            membername: str,
                            isattr: bool,
                            parent: Any) -> bool:
        try:
            return issubclass(member, IntFlag)
        except TypeError:
            return False

    def apply_options(self, obj: IntFlag) -> str:
        fill = self.options.fill if self.options.fill else 0
        return f"= 0x{obj:0{fill}{'x' if self.options.hex else ''}}"

    def document_members(self, all_members: bool = False):
        """Generatere rST for member documentation.
           If *all_members* is True, document all members, else those
          given by *self.options.members*.

          NOTE THIS IS MODIFIED FROM 
          sphinx.ext.autodoc.__init__ : class Documenter
        """
        # set current namespace for finding members 
        self.env.temp_data['autodoc:module'] = self.modname 
        if self.objpath:
            self.env.temp_data['autodoc:class'] = self.objpath[0] 

        want_all = (all_members or 
                    self.options.inherited_members or 
                    self.options.members is ALL) 
        # find out which members are documentable 
        members_check_module, members = self.get_object_members(want_all) 
                             
        # document non-skipped members 
        memberdocumenters: list[tuple[Documenter, bool]] = [] 

        for (mname, member, isattr) in self.filter_members(members, want_all): 
            classes = [cls for cls in self.documenters.values() 
                       if cls.can_document_member(member, mname, isattr, self)] 
            if not classes: 
                # don't know how to document this member 
                continue 

            # prefer the documenter with the highest priority 
            classes.sort(key = lambda cls: cls.priority) 
            # give explicitly separated module name,so that members 
            # of inner classes can be documented 
            full_mname = self.modname + '::' + '.'.join(self.objpath + [mname]) 
            documenter = classes[-1](self.directive, full_mname, self.indent) 
            memberdocumenters.append((documenter, isattr, member)) 
                                                     
        member_order = (self.options.member_order
                        or self.config.autodoc_member_order)
        memberdocumenters = self.sort_members(memberdocumenters, member_order) 
                                                         
        for documenter, isattr, member in memberdocumenters: 
            if isattr and self.options.hex:
                documenter.options.annotation = self.apply_options(member)
            documenter.generate( 
                all_members=True, real_modname=self.real_modname, 
                check_module=members_check_module and not isattr) 
        
        # reset current objects
        self.env.temp_data['autodoc:module'] = None 
        self.env.temp_data['autodoc:class'] = None


def setup(app: Sphinx):
    app.setup_extension("sphinx.ext.autodoc")
    app.add_autodocumenter(IntFlagDocumenter)

