%global bundled_dir %{_libdir}/%{name}/bundled

%global _privatelibs libdouble-conversion[.]so.*
%global _privatelibs %{_privatelibs}|libgdl-3[.]so.*

%global __provides_exclude ^(%{_privatelibs})$
%global __requires_exclude ^(%{_privatelibs})$

Name:           inkscape1
Version:        1.0.2
Release:        3%{?dist}
Summary:        Vector-based drawing program using SVG

License:        GPLv2+ and CC-BY
URL:            https://inkscape.org/
Source0:        https://inkscape.org/gallery/item/23820/inkscape-1.0.2.tar.xz

# Fedora Color Palette, GIMP format, CC-BY 3.0
Source2:        Fedora-Color-Palette.gpl
Source3:        double-conversion-3.1.5-6.el9.src.rpm
Source4:        libgdl-3.34.0-3.fc33.src.rpm

Patch1:         cmake-gnuinstalldirs.patch

BuildRequires:  gcc-c++
BuildRequires:  aspell-devel aspell-en
BuildRequires:  atk-devel
BuildRequires:  boost-devel
BuildRequires:  cairo-devel
BuildRequires:  dos2unix
BuildRequires:  desktop-file-utils
BuildRequires:  freetype-devel
BuildRequires:  gc-devel >= 6.4
BuildRequires:  gettext
BuildRequires:  gsl-devel
BuildRequires:  gtkmm30-devel
BuildRequires:  gtkspell3-devel
BuildRequires:  intltool
BuildRequires:  lcms2-devel
BuildRequires:  libpng-devel >= 1.2
BuildRequires:  libwpg-devel
BuildRequires:  libxml2-devel >= 2.6.11
BuildRequires:  libxslt-devel >= 1.0.15
BuildRequires:  pango-devel
BuildRequires:  pkgconfig
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  poppler-glib-devel
BuildRequires:  popt-devel
BuildRequires:  libappstream-glib
BuildRequires:  libtool
BuildRequires:  potrace-devel
BuildRequires:  cmake
BuildRequires:  libwpd-devel
BuildRequires:  dbus-glib-devel
BuildRequires:  libjpeg-devel
BuildRequires:  libsigc++20-devel
BuildRequires:  libsoup-devel
BuildRequires:  make

# libgdl build requires
BuildRequires:  gobject-introspection-devel
BuildRequires:  gtk3-devel
BuildRequires:  gtk-doc
BuildRequires:  perl(XML::Parser)


# Disable all for now. TODO: Be smarter
%if 0
Requires:       dia
Requires:       ghostscript
Requires:       perl(Image::Magick)
Requires:       transfig
Requires:       gimp
%endif
Requires:       python3
Requires:       python3-lxml
Requires:       python3-numpy
Requires:       python3-scour

# Weak dependencies for the LaTeX plugin
Suggests:       pstoedit
Suggests:       tex(latex)
Suggests:       tex(dvips)
Suggests:       texlive-amsmath
Suggests:       texlive-amsfonts

Obsoletes:      inkscape < 0.92.3-17

Provides:       bundled(libcroco) = 0.6
Provides:       bundled(libgdl) = 3.34.0-3
Provides:       bundled(double-conversion) = 3.1.5-3

%description
Inkscape is a vector graphics editor, with capabilities similar to
Illustrator, CorelDraw, or Xara X, using the W3C standard Scalable Vector
Graphics (SVG) file format.  It is therefore a very useful tool for web
designers and as an interchange format for desktop publishing.

Inkscape supports many advanced SVG features (markers, clones, alpha
blending, etc.) and great care is taken in designing a streamlined
interface. It is very easy to edit nodes, perform complex path operations,
trace bitmaps and much more.

%package view
Summary:        Viewing program for SVG files
Requires:       %{name} = %{version}-%{release}

Obsoletes:      inkscape-view < 0.92.3-17

%description view
Viewer for files in W3C standard Scalable Vector Graphics (SVG) file
format.


%package docs
Summary:        Documentation for Inkscape

Obsoletes:      inkscape-docs < 0.92.3-17

%description docs
Tutorial and examples for Inkscape, a graphics editor for vector
graphics in W3C standard Scalable Vector Graphics (SVG) file format.


%prep
%autosetup -n inkscape-1.0.2_2021-01-15_e86c870879 -p1
pathfix.py -pni "%{__python3} %{py3_shbang_opts}" .
find . -name CMakeLists.txt | xargs sed -i 's|COMMAND python |COMMAND %{__python3} |g'

#strip invalid tag
sed -i /url/d org.inkscape.Inkscape.appdata.xml.in

# https://bugs.launchpad.net/inkscape/+bug/314381
# A couple of files have executable bits set,
# despite not being executable
find . -name '*.cpp' | xargs chmod -x
find . -name '*.h' | xargs chmod -x

# Fix end of line encodings
dos2unix -k -q share/extensions/*.py

%build
BUNDLED_PREFIX="%{_topdir}/RPMS"
function build_bundled_library() {
  PACKAGE_RPM=$1
  PACKAGE_SOURCE=$2
  PACKAGE_DIR="%{_topdir}/RPMS"

  echo "Rebuilding library $PACKAGE_RPM from $PACKAGE_SOURCE for bundling"; echo "==============================="
  rpmbuild --showrc
  rpmbuild --nodeps --define '_prefix %{bundled_dir}' --define 'debug_package %%{nil}' --rebuild $PACKAGE_SOURCE || exit 1
  if [ ! -f $PACKAGE_DIR/$PACKAGE_RPM ]; then
    # Hack for tps tests
    ARCH_STR=%{_arch}
    %ifarch i386 i686
    ARCH_STR="i?86"
    %endif
    PACKAGE_DIR="$PACKAGE_DIR/$ARCH_STR"
  fi
  # Get rid of -debug package that we don't unpack them later
  rm -f $PACKAGE_DIR/*debug*.rpm
  # Unpack all rpm with given name to the .../rpmbuild/bundle
  for rpm in $PACKAGE_DIR/$PACKAGE_RPM; do
    echo "Installing $rpm to $BUNDLED_PREFIX"; echo "==============================="
    pushd $BUNDLED_PREFIX
    rpm2cpio $rpm | cpio -iduv
    #rm -f $rpm
    popd
  done
}

function install_rpms_to_current_dir() {
  PACKAGE_RPM=$(eval echo $1)
  PACKAGE_DIR="%{_topdir}/RPMS"
  echo "Installing $PACKAGE_RPM to (current dir) `pwd`"

  if [ ! -f $PACKAGE_DIR/$PACKAGE_RPM ]; then
    # Hack for tps tests
    ARCH_STR=%{_arch}
    %ifarch i386 i686
      ARCH_STR="i?86"
    %endif
    %if 0%{?rhel} > 6
      PACKAGE_DIR="$PACKAGE_DIR/$ARCH_STR"
    %endif
  fi
  for package in $(ls $PACKAGE_DIR/$PACKAGE_RPM)
  do
    echo "$package"
    rpm2cpio "$package" | cpio -idu
  done
}

%if 0%{?flatpak}
export DEVLIBS_PATH=/app
%endif

# Build and install locally the bundled libraries before the main build
build_bundled_library 'libgdl-*.rpm' '%{SOURCE4}'
pushd %{_buildrootdir}
install_rpms_to_current_dir libgdl-*.rpm
popd

export PKG_CONFIG_PATH=%{_buildrootdir}%{bundled_dir}/%{_lib}/pkgconfig
sed -i 's@%{bundled_dir}@%{_buildrootdir}%{bundled_dir}@g' %{_buildrootdir}%{bundled_dir}/%{_lib}/pkgconfig/gdl*.pc
build_bundled_library 'double-conversion-*.rpm' '%{SOURCE3}'
pushd %{_buildrootdir}
install_rpms_to_current_dir double-conversion-*.rpm
popd

export CMAKE_PREFIX_PATH=$BUNDLED_PREFIX/%{bundled_dir}/%{_lib}
export CMAKE_FIND_ROOT_PATH="$BUNDLED_PREFIX/%{bundled_dir}/;%{_prefix}"
echo "==============================="
echo "Building Inkscape"
echo "==============================="
%cmake3 \
        -DCMAKE_SHARED_LINKER_FLAGS:STRING="$LDFLAGS -L$BUNDLED_PREFIX%{_libdir} -Wl,-rpath,%{bundled_dir}/%{_lib} -Wl,-rpath-link,%{_buildrootdir}/%{bundled_dir}/%{_lib}" \
        -DCMAKE_EXE_LINKER_FLAGS:STRING="$LDFLAGS -L$BUNDLED_PREFIX%{_libdir} -Wl,-rpath,/%{bundled_dir}/%{_lib} -Wl,-rpath-link,%{_buildrootdir}%/%{bundled_dir}/%{_lib}" \
        -DCMAKE_VERBOSE_MAKEFILE:BOOL=ON \
        -DBUILD_SHARED_LIBS:BOOL=OFF \
        -DCMAKE_PREFIX_PATH="$BUNDLED_PREFIX/%{bundled_dir}/%{_lib}" \
        -DCMAKE_FIND_ROOT_PATH="$BUNDLED_PREFIX/%{bundled_dir}/;%{_prefix}" \
%cmake_build


%install
function install_rpms_to_current_dir() {
  PACKAGE_RPM=$(eval echo $1)
  PACKAGE_DIR="%{_topdir}/RPMS"
  echo "Installing $PACKAGE_RPM to (current dir) `pwd`"

  if [ ! -f $PACKAGE_DIR/$PACKAGE_RPM ]; then
    # Hack for tps tests
    ARCH_STR=%{_arch}
    %ifarch i386 i686
      ARCH_STR="i?86"
    %endif
    %if 0%{?rhel} > 6
      PACKAGE_DIR="$PACKAGE_DIR/$ARCH_STR"
    %endif
  fi
  for package in $(ls $PACKAGE_DIR/$PACKAGE_RPM)
  do
    echo "$package"
    rpm2cpio "$package" | cpio -idu
  done
}
# install bundled libraries
pushd %{buildroot}
install_rpms_to_current_dir libgdl-3*.rpm
install_rpms_to_current_dir double-conversion-3*.rpm
rm -rf usr/lib/.build-id
popd

#cleanup  unwanted rpms:
rm -f %{_topdir}/RPMS/double-conversion*
rm -f %{_topdir}/RPMS/libgdl*

%cmake_install

find $RPM_BUILD_ROOT -type f -name 'lib*.a' | xargs rm -f

# No skencil anymore
rm -f $RPM_BUILD_ROOT%{_datadir}/%{name}/extensions/sk2svg.sh

# Install Fedora Color Pallette
install -pm 644 %{SOURCE2} $RPM_BUILD_ROOT%{_datadir}/inkscape/palettes/

%find_lang inkscape --with-man

rm -rf $RPM_BUILD_ROOT%{_datadir}/inkscape/doc
rm -f $RPM_BUILD_ROOT%{_datadir}/doc/inkscape/copyright


%check
# Validate appdata file
appstream-util validate-relax --nonet $RPM_BUILD_ROOT%{_datadir}/metainfo/*.appdata.xml

# Validate desktop file
desktop-file-validate $RPM_BUILD_ROOT%{_datadir}/applications/org.inkscape.Inkscape.desktop


%files -f inkscape.lang
%{!?_licensedir:%global license %%doc}
%license COPYING
%doc AUTHORS NEWS.md README.md
%{_bindir}/inkscape
%dir %{_datadir}/inkscape
%{_datadir}/inkscape/attributes
%{_datadir}/inkscape/branding
%{_datadir}/inkscape/extensions
# Pulls in perl, if needed should go into a -perl subpackage
%if 0%{?flatpak}
# Pulls in ruby
%exclude %{_datadir}/inkscape/extensions/simplepath.rb
%endif
%{_datadir}/inkscape/filters
%{_datadir}/inkscape/fonts
%{_datadir}/inkscape/icons
%{_datadir}/inkscape/keys
%{_datadir}/inkscape/markers
%{_datadir}/inkscape/palettes
%{_datadir}/inkscape/paint
%{_datadir}/inkscape/pixmaps
%{_datadir}/inkscape/screens
%{_datadir}/inkscape/symbols
%{_datadir}/inkscape/templates
%{_datadir}/inkscape/ui
%{_datadir}/metainfo/org.inkscape.Inkscape.appdata.xml
%{_datadir}/applications/org.inkscape.Inkscape.desktop
%{_mandir}/man1/*.1*
%exclude %{_mandir}/man1/inkview.1*
%{_datadir}/inkscape/tutorials
%{_datadir}/icons/hicolor/*/apps/*.png
%{_datadir}/bash-completion/completions/inkscape
%{bundled_dir}

%files view
%{!?_licensedir:%global license %%doc}
%license COPYING
%doc AUTHORS NEWS.md README.md
%{_bindir}/inkview
%{_mandir}/man1/inkview.1*
%{_mandir}/*/man1/inkview.1*


%files docs
%license COPYING
%dir %{_datadir}/inkscape
%{_datadir}/inkscape/examples


%changelog
* Thu May 25 2023 Kyle Walker <kwalker@redhat.com> - 1.0.2-3
- Remove the Provides RPM tags
- Resolves: rhbz#2209988

* Thu Oct 20 2022 Tomas Popela <tpopela@redhat.com> - 1.0.2-2
- Fix the rpath by backporting an upstream patch
- Add gating.yaml
- Resolves: rhbz#1891732

* Tue Oct 18 2022 Tomas Popela <tpopela@redhat.com> - 1.0.2-1
- Bring Inkscape 1.0.1 into RHEL 8.8 and obsolete the previous 0.92.3 modular
  package. See https://issues.redhat.com/browse/RHELPLAN-121672
- Resolves: rhbz#1891732

* Wed Jul 10 2019 Jan Horak <jhorak@redhat.com> - 0.92.3-13
- Rebuild due to newer poppler

* Mon Oct 15 2018 Jan Horak <jhorak@redhat.com> - 0.92.3-11
- Fixed cflags and inkscape-view dependency

* Wed Sep  5 2018 Jan Horak <jhorak@redhat.com> - 0.92.3-10
- Stop using bundled ImageMagick

* Thu Aug  9 2018 Jan Horak <jhorak@redhat.com> - 0.92.3-8
- Filtering magick from requires/provides
- Removed libgdl depedency

* Wed Jul 25 2018 Jan Horak <jhorak@redhat.com> - 0.92.3-6
- Enable s390x again

* Fri Jul 13 2018 Jan Horak <jhorak@redhat.com> - 0.92.3-5
- Use python2 for building
- Fix building with poppler 0.66.0

* Tue May 22 2018 Jan Horak <jhorak@redhat.com> - 0.92.3-3
- Use python2 for the extensions explicitly
- Exluding s390x, build problems, making no sense to build Inkscape for
  mainframe hardware

* Thu May 10 2018 Jan Horak <jhorak@redhat.com> - 0.92.3-2
- Bundle ImageMagick into the package
- Removed gnome-vfs2-devel requirement
- Make uniconvertor weak dependency

* Tue Apr 17 2018 Gwyn Ciesla <limburgher@gmail.com> - 0.92.3-1
- 0.92.3.

* Fri Mar 23 2018 Marek Kasik <mkasik@redhat.com> - 0.92.2-8
- Rebuild for poppler-0.63.0

* Thu Mar 01 2018 Iryna Shcherbina <ishcherb@redhat.com> - 0.92.2-7
- Update Python 2 dependency declarations to new packaging standards
  (See https://fedoraproject.org/wiki/FinalizingFedoraSwitchtoPython3)

* Wed Feb 14 2018 David Tardon <dtardon@redhat.com> - 0.92.2-6
- rebuild for poppler 0.62.0

* Wed Feb 07 2018 Fedora Release Engineering <releng@fedoraproject.org> - 0.92.2-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Thu Jan 11 2018 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 0.92.2-4
- Remove obsolete scriptlets

* Wed Nov 08 2017 David Tardon <dtardon@redhat.com> - 0.92.2-3
- rebuild for poppler 0.61.0

* Fri Oct 06 2017 David Tardon <dtardon@redhat.com> - 0.92.2-2
- rebuild for poppler 0.60.1

* Mon Sep 25 2017 Gwyn Ciesla <limburgher@gmail.com> - 0.92.2-1
- 0.92.2 final.

* Fri Sep 08 2017 David Tardon <dtardon@redhat.com> - 0.92.1-15.20170713bzr15740
- rebuild for poppler 0.59.0

* Tue Sep 05 2017 Adam Williamson <awilliam@redhat.com> - 0.92.1-14.20170713bzr15740
- Rebuild for ImageMagick 6 reversion, drop ImageMagick 7 patch

* Sun Aug 27 2017 Ville Skyttä <ville.skytta@iki.fi> - 0.92.1-13.20170713bzr15740
- Own the /usr/lib/inkscape dir
- %%langify non-English man pages

* Fri Aug 25 2017 Michael Cronenworth <mike@cchtml.com> - 0.92.1-12.20170713bzr15740
- Rebuilt for ImageMagick

* Tue Aug 08 2017 Gwyn Ciesla <limburgher@gmail.com> - 0.92.1-11.20170713bzr15740
- Require aspell-en

* Thu Aug 03 2017 David Tardon <dtardon@redhat.com> - 0.92.1-10.20170713bzr15740
- rebuild for poppler 0.57.0

* Wed Aug 02 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.92.1-9.20170713bzr15740
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Sun Jul 30 2017 Kevin Fenzi <kevin@scrye.com> - 0.92.1-8.20170713bzr15740
- Rebuilt for ImageMagick

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.92.1-7.20170713bzr15740
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Thu Jul 13 2017 Gwyn Ciesla <limburgher@gmail.com> - 0.92.1-6.20170713bzr15740
- Updated snapshot.

* Fri Jun 23 2017 Gwyn Ciesla <limburgher@gmail.com> - 0.92.1-5.20170510bzr15686
- Move from gtkspell to gtkspell3, BZ 1464487.

* Wed May 10 2017 Gwyn Ciesla <limburgher@gmail.com> - 0.92.1-4.20170510bzr15686
- Update to fix on Wayland.
- Fix CFLAGS.

* Tue Mar 28 2017 David Tardon <dtardon@redhat.com> - 0.92.1-3.20170321bzr15604
- rebuild for poppler 0.53.0

* Tue Mar 21 2017 Gwyn Ciesla <limburgher@gmail.com> - 0.92.1-2.20170321bzr15604
- Snapshot to fix gcc7 FTBFS.

* Thu Feb 16 2017 Jon Ciesla <limburgher@gmail.com> - 0.92.1-1
- 0.92.1 final.

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.92.0-12
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Thu Jan 05 2017 Jon Ciesla <limburgher@gmail.com> - 0.92.0-11
- 0.92 final.

* Fri Dec 30 2016 Jon Ciesla <limburgher@gmail.com> - 0.92-10.pre5
- 0.92pre5.

* Thu Dec 22 2016 Jon Ciesla <limburgher@gmail.com> - 0.92-9.pre4
- 0.92pre4.

* Fri Dec 16 2016 David Tardon <dtardon@redhat.com> - 0.92-8.pre3
- rebuild for poppler 0.50.0

* Mon Nov 28 2016 Jon Ciesla <limburgher@gmail.com> - 0.92-7.pre3
- 0.92pre3.
- Include Fedora Color Palette, BZ 981748

* Wed Nov 23 2016 David Tardon <dtardon@redhat.com> - 0.92-6.pre2
- rebuild for poppler 0.49.0

* Fri Oct 28 2016 Jon Ciesla <limburgher@gmail.com> - 0.92-5.pre2
- Require python-scour, BZ 1389772.

* Fri Oct 28 2016 Jon Ciesla <limburgher@gmail.com> - 0.92-4.pre2
- BR potrace-devel, BZ 1389772.

* Fri Oct 21 2016 Jon Ciesla <limburgher@gmail.com> - 0.92-3.pre2
- Fix release tag.

* Fri Oct 21 2016 Marek Kasik <mkasik@redhat.com> - 0.92-2.pre2
- Rebuild for poppler-0.48.0

* Wed Oct 19 2016 Jon Ciesla <limburgher@gmail.com> - 0.92-0.pre2
- 0.92pre2.

* Mon Jul 18 2016 Marek Kasik <mkasik@redhat.com> - 0.92-1.pre1
- Rebuild for poppler-0.45.0

* Tue Jun 14 2016 Jon Ciesla <limburgher@gmail.com> - 0.92-0.pre1
- 0.92pre1.
- Drop docs requirement on main package, BZ 1247239.

* Tue May 17 2016 Jon Ciesla <limburgher@gmail.com> - 0.92-0.pre0
- 0.92pre0, BZ 1336412.

* Tue May  3 2016 Marek Kasik <mkasik@redhat.com> - 0.91-27
- Rebuild for poppler-0.43.0

* Fri Apr 08 2016 Jon Ciesla <limburgher@gmail.com> - 0.91-26
- Fix FTBFS with patch from https://bugzilla.gnome.org/show_bug.cgi?id=586626

* Mon Feb 22 2016 Orion Poplawski <orion@cora.nwra.com>
- Rebuild for gsl 2.1

* Tue Feb 16 2016 Jonathan Underwood <jonathan.underwood@gmail.com> - 0.91-24
- Add Requires for gvfs

* Mon Feb 15 2016 Jonathan Underwood <jonathan.underwood@gmail.com> - 0.91-23
- Break appdata file out of spec into its own file
- Validate appdata file once installed
- Add BuildRequires for libappstream-glib (provides appstream-util)
- Remove commented out line in file list
- Re-add export CXXFLAGS="%%{optflags} -std=c++11" to fix build

* Mon Feb 15 2016 Jonathan Underwood <jonathan.underwood@gmail.com> - 0.91-22
- Drop --disable-strict-build since this is fixed:
  https://bugzilla.gnome.org/show_bug.cgi?id=752797
- Drop export CXXFLAGS="%%{optflags} -std=c++11" since that's now default

* Mon Feb 15 2016 Jonathan Underwood <jonathan.underwood@gmail.com> - 0.91-21
- Remove BuildRequires for  gnome-vfs2-devel

* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 0.91-20
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Fri Jan 22 2016 Marek Kasik <mkasik@redhat.com> - 0.91-19
- Rebuild for poppler-0.40.0

* Fri Jan 15 2016 Jonathan Wakely <jwakely@redhat.com> - 0.91-18
- Rebuilt for Boost 1.60

* Wed Sep 23 2015 Kalev Lember <klember@redhat.com> - 0.91-17
- Fix the build with latest glibmm24

* Thu Aug 27 2015 Jonathan Wakely <jwakely@redhat.com> - 0.91-16
- Rebuilt for Boost 1.59

* Wed Aug 05 2015 Jonathan Wakely <jwakely@redhat.com> 0.91-15
- Rebuilt for Boost 1.58

* Tue Aug  4 2015 Jonathan Underwood <jonathan.underwood@gmail.com> - 0.91-14
- Remove some entries from unused Requires block that we now
  explicitly Require or Suggests.

* Tue Aug  4 2015 Jonathan Underwood <jonathan.underwood@gmail.com> - 0.91-13
- Add Suggests deps for packages needed to enable LaTeX fragment
  embedding

* Wed Jul 29 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.91-12
- Rebuilt for https://fedoraproject.org/wiki/Changes/F23Boost159

* Thu Jul 23 2015 Adam Williamson <awilliam@redhat.com> - 0.91-11
- --disable-strict-build (as gtkmm currently uses a deprecated glibmm symbol)

* Wed Jul 22 2015 David Tardon <dtardon@redhat.com>
- rebuild for Boost 1.58

* Wed Jul 22 2015 Marek Kasik <mkasik@redhat.com> - 0.91-10
- Rebuild (poppler-0.34.0)

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.91-9
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Fri Jun  5 2015 Marek Kasik <mkasik@redhat.com> - 0.91-8
- Rebuild (poppler-0.33.0)

* Wed Apr 29 2015 Kalev Lember <kalevlember@gmail.com> - 0.91-7
- Rebuilt for GCC 5 ABI change

* Thu Mar 26 2015 Richard Hughes <rhughes@redhat.com> - 0.91-6
- Add an AppData file for the software center

* Fri Mar 06 2015 Jon Ciesla <limburgher@gmail.com> - 0.91-5
- ImageMagick rebuild.

* Thu Feb 12 2015 Peter Robinson <pbrobinson@fedoraproject.org> 0.91-4
- Cleanup spec
- Use %%license
- Drop (now unneeded) perl requirements (rhbz#579390)
- Drop ChangeLog as details are covered in NEWS

* Wed Feb 04 2015 Petr Machata <pmachata@redhat.com> - 0.91-3
- Bump for rebuild.

* Fri Jan 30 2015 Jon Ciesla <limburgher@gmail.com> - 0.91-2
- Move tutorials into main package, BZ 1187686.

* Thu Jan 29 2015 Jon Ciesla <limburgher@gmail.com> - 0.91-1
- Latest upstream.

* Tue Jan 27 2015 Petr Machata <pmachata@redhat.com> - 0.48.5-7
- Rebuild for boost 1.57.0

* Fri Jan 23 2015 Marek Kasik <mkasik@redhat.com> - 0.48.5-6
- Rebuild (poppler-0.30.0)
- Backport commit "Fix build with poppler 0.29.0 (Bug #1399811)"

* Fri Jan 09 2015 Jon Ciesla <limburgher@gmail.com> - 0.48.5-5
- Added aspell support, BZ 1171934.

* Thu Nov 27 2014 Marek Kasik <mkasik@redhat.com> - 0.48.5-4
- Rebuild (poppler-0.28.1)

* Thu Aug 28 2014 Jitka Plesnikova <jplesnik@redhat.com> - 0.48.5-3
- Perl 5.20 rebuild

* Sat Aug 16 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.48.5-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Mon Jul 21 2014 Jon Ciesla <limburgher@gmail.com> - 0.48.5-1
- Latest bugfix release.
- Spurious comma patch upstreamed.
- Dropped Freetype, poppler, gc patches.

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.48.4-18
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Tue Jun 03 2014 Jon Ciesla <limburgher@gmail.com> - 0.48.4-17
- Switch to lcms2.

* Tue May 27 2014 David Tardon <dtardon@redhat.com> - 0.48.4-16
- switch to librevenge-based import libs

* Fri May 23 2014 Petr Machata <pmachata@redhat.com> - 0.48.4-15
- Rebuild for boost 1.55.0

* Thu May 15 2014 Lubomir Rintel <lkundrak@v3.sk> - 0.48.4-14
- Fix build with new Poppler and GC (Sandro Mani, #1097945)

* Wed May 14 2014 Jon Ciesla <limburgher@gmail.com> - 0.48.4-13
- poppler rebuild.

* Mon Mar 31 2014 Jon Ciesla <limburgher@gmail.com> - 0.48.4-12
- ImageMagick rebuild.
- Patch for Freetype path.

* Wed Oct 09 2013 Jon Ciesla <limburgher@gmail.com> - 0.48.4-11
- ImageMagick rebuild.

* Mon Aug 19 2013 Marek Kasik <mkasik@redhat.com> - 0.48.4-10
- Rebuild (poppler-0.24.0)

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.48.4-9
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Tue Jul 30 2013 Petr Machata <pmachata@redhat.com> - 0.48.4-8
- Rebuild for boost 1.54.0

* Wed Jul 24 2013 Petr Pisar <ppisar@redhat.com> - 0.48.4-7
- Perl 5.18 rebuild

* Tue Jun 25 2013 Jon Ciesla <limburgher@gmail.com> - 0.48.4-6
- libpoppler rebuild.

* Mon Mar 18 2013 Jon Ciesla <limburgher@gmail.com> - 0.48.4-5
- ImageMagick rebuild.

* Fri Feb 15 2013 Jon Ciesla <limburgher@gmail.com> - 0.48.4-4
- Fix FTBFS.

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.48.4-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Fri Jan 18 2013 Marek Kasik <mkasik@redhat.com> - 0.48.4-2
- Rebuild (poppler-0.22.0)

* Thu Dec 06 2012 Jon Ciesla <limburgher@gmail.com> - 0.48.3.1-4
- 0.48.4, fix XXE security flaw.
- Correct man page ownership.

* Thu Dec 06 2012 Jon Ciesla <limburgher@gmail.com> - 0.48.3.1-4
- Fix directory ownership, BZ 873817.
- Fix previous changelog version.

* Mon Nov 19 2012 Nils Philippsen <nils@redhat.com> - 0.48.3.1-3
- update sourceforge download URL

* Thu Nov 01 2012 Jon Ciesla <limburgher@gmail.com> - 0.48.3.1-2
- Allow loading large XML, BZ 871012.

* Fri Oct 05 2012 Jon Ciesla <limburgher@gmail.com> - 0.48.3.1-1
- Lastest upstream.

* Thu Oct 04 2012 Jon Ciesla <limburgher@gmail.com> - 0.48.2-13
- Added dep on uniconvertor, BZ 796424.

* Thu Jul 19 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.48.2-12
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Mon Jul 09 2012 Petr Pisar <ppisar@redhat.com> - 0.48.2-11
- Perl 5.16 rebuild

* Mon Jul  2 2012 Marek Kasik <mkasik@redhat.com> - 0.48.2-10
- Rebuild (poppler-0.20.1)

* Wed Jun 27 2012 Petr Pisar <ppisar@redhat.com> - 0.48.2-9
- Perl 5.16 rebuild

* Sat Jun 23 2012 Rex Dieter <rdieter@fedoraproject.org> 
- 0.48.2-8
- fix icon/desktop-file scriptlets (#739375)
- drop .desktop vendor (f18+)
- inkscape doesn't build with poppler-0.20.0 (#822413)

* Fri Jun 15 2012 Petr Pisar <ppisar@redhat.com> - 0.48.2-7
- Perl 5.16 rebuild

* Mon Jun 11 2012 Adel Gadllah <adel.gadllah@gmail.com> - 0.48.2-6
- Rebuild for new poppler

* Wed Apr 11 2012 Peter Robinson <pbrobinson@fedoraproject.org> - 0.48.2-5
- Rebuild for ImageMagik

* Thu Mar  8 2012 Daniel Drake <dsd@laptop.org> - 0.48.2-4
- Fix build with GCC 4.7

* Tue Feb 28 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.48.2-3
- Rebuilt for c++ ABI breakage

* Fri Jan 13 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.48.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Tue Nov 15 2011 German Ruiz <germanrs@fedoraproject.org> - 0.48.2-1
- New upstream version
- Fix glib include compile problem
- Fix compilation against libpng-1.5

* Fri Oct 28 2011 Rex Dieter <rdieter@fedoraproject.org> - 0.48.1-10
- rebuild(poppler)

* Fri Sep 30 2011 Marek Kasik <mkasik@redhat.com> - 0.48.1-9
- Rebuild (poppler-0.18.0)

* Mon Sep 19 2011 Marek Kasik <mkasik@redhat.com> - 0.48.1-8
- Rebuild (poppler-0.17.3)

* Thu Jul 21 2011 Petr Sabata <contyk@redhat.com> - 0.48.1-7
- Perl mass rebuild

* Tue Jul 19 2011 Petr Sabata <contyk@redhat.com> - 0.48.1-6
- Perl mass rebuild

* Fri Jul 15 2011 Marek Kasik <mkasik@redhat.com> - 0.48.1-5
- Rebuild (poppler-0.17.0)

* Sun Mar 13 2011 Marek Kasik <mkasik@redhat.com> - 0.48.1-4
- Rebuild (poppler-0.16.3)

* Wed Feb 09 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.48.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Wed Feb 09 2011 Lubomir Rintel <lkundrak@v3.sk> - 0.48.1-2
- Re-enable GVFS for OCAL

* Mon Feb 07 2011 Lubomir Rintel <lkundrak@v3.sk> - 0.48.1-1
- Bump release

* Fri Feb 04 2011 Lubomir Rintel <lkundrak@v3.sk> - 0.48.0-10
- Drop gnome-vfs requirement
- Fix Rawhide build

* Sat Jan 01 2011 Rex Dieter <rdieter@fedoraproject.org> - 0.48.0-9
- rebuild (poppler)

* Wed Dec 15 2010 Rex Dieter <rdieter@fedoraproject.org> - 0.48.0-8
- rebuild (poppler)

* Wed Dec 08 2010 Caolán McNamara <caolanm@redhat.com> - 0.48.0-7
- rebuilt (libwpd)

* Sun Nov 14 2010 Lubomir Rintel <lkundrak@v3.sk> - 0.48.0-6
- rebuilt (poppler)

* Tue Oct 05 2010 Nils Philippsen <nils@redhat.com> - 0.48.0-5
- Rebuild for poppler update

* Wed Sep 29 2010 jkeating - 0.48.0-4
- Rebuilt for gcc bug 634757

* Wed Sep 29 2010 Dan Horák <dan[at]danny.cz> - 0.48.0-3
- drop the s390(x) ExcludeArch

* Mon Sep 20 2010 Tom "spot" Callaway <tcallawa@redhat.com> - 0.48.0-2
- rebuild for new ImageMagick

* Wed Aug 25 2010 Lubomir Rintel <lkundrak@v3.sk> - 0.48.0-1
- New upstream release
- Drop el5 support

* Thu Aug 19 2010 Rex Dieter <rdieter@fedoraproject.org> - 0.48-0.5.20100505bzr
- rebuild (poppler)

* Tue Jul 27 2010 David Malcolm <dmalcolm@redhat.com> - 0.48-0.4.20100505bzr
- Rebuilt for https://fedoraproject.org/wiki/Features/Python_2.7/MassRebuild

* Tue Jun 01 2010 Marcela Maslanova <mmaslano@redhat.com> - 0.48-0.3.20100505bzr
- Mass rebuild with perl-5.12.0

* Wed May 05 2010 Lubomir Rintel <lkundrak@v3.sk> - 0.48-0.2.20100505bzr
- Move to later snapshot
- Drop uniconvertor patch

* Tue Apr 06 2010 Caolán McNamara <caolanm@redhat.com> - 0.48-0.2.20100318bzr
- Resolves: rhbz#565106 fix inkscape-0.47-x11.patch to not clobber INKSCAPE_LIBS

* Thu Mar 18 2010 Lubomir Rintel <lkundrak@v3.sk> - 0.48-0.1.20100318bzr
- Update to latest bazaar snapshot

* Thu Feb 18 2010 Lubomir Rintel <lkundrak@v3.sk> - 0.47-7
- Fix build

* Wed Jan 20 2010 Stepan Kasal <skasal@redhat.com> - 0.47-6
- ExcludeArch: s390 s390x

* Fri Jan 15 2010 Stepan Kasal <skasal@redhat.com> - 0.47-5
- require perl(:MODULE_COMPAT_5.10.x) because the package requires libperl.so
- the same for inkscape-view

* Fri Jan  8 2010 Owen Taylor <otaylor@redhat.com> - 0.47-4
- Remove loudmouth BuildRequires; there is no current usage of loudmouth in the code

* Sun Dec 06 2009 Lubomir Rintel <lkundrak@v3.sk> - 0.47-2
- Fix Rawhide build.

* Wed Nov 25 2009 Lubomir Rintel <lkundrak@v3.sk> - 0.47-1
- Stable release

* Mon Nov 23 2009 Adam Jackson <ajax@redhat.com> 0.47-0.18.pre4.20091101svn
- Fix RHEL6 build.

* Mon Sep 07 2009 Lubomir Rintel <lkundrak@v3.sk> - 0.47-0.17.pre4.20091101svn
- Icon for main window (#532325)

* Mon Sep 07 2009 Lubomir Rintel <lkundrak@v3.sk> - 0.47-0.16.pre4.20091101svn
- Move to a later snapshot
- python-lxml and numpy seem to be rather popular, add them as hard deps

* Mon Sep 07 2009 Lubomir Rintel <lkundrak@v3.sk> - 0.47-0.16.pre3.20091017svn
- Move to a later snapshot

* Mon Sep 07 2009 Lubomir Rintel <lkundrak@v3.sk> - 0.47-0.16.pre3.20090925svn
- Move to a later snapshot
- Drop debugging compiler flags, enable optimizations again
- Make it build on everything since EL5 again

* Mon Sep 07 2009 Lubomir Rintel <lkundrak@v3.sk> - 0.47-0.16.pre2.20090907svn
- Move inkview man page to -view subpackage (#515358)
- Add license, etc. to main package

* Mon Sep 07 2009 Lubomir Rintel <lkundrak@v3.sk> - 0.47-0.15.pre2.20090907svn
- Update to a post-pre2 snapshot

* Mon Aug 10 2009 Lubomir Rintel <lkundrak@v3.sk> - 0.47-0.15.pre1.20090629svn
- Update to a post-pre1 snapshot
- Drop upstreamed CRC32 fix

* Fri Jul 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.47-0.14.pre0.20090629svn
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Mon Jun 29 2009 Lubomir Rintel <lkundrak@v3.sk> - 0.47-0.13.pre0.20090629svn
- Update to a newer snapshot

* Tue Jun 16 2009 Lubomir Rintel <lkundrak@v3.sk> - 0.47-0.12.pre0.20090616svn
- Update to post-pre0 snapshot

* Tue Jun 02 2009 Lubomir Rintel <lkundrak@v3.sk> - 0.47-0.11.20090602svn
- More recent snapshot
- Upstream removed rasterized icons again

* Sat May 23 2009 Lubomir Rintel <lkundrak@v3.sk> - 0.47-0.10.20090518svn
- Rebuild for new poppler

* Mon May 18 2009 Lubomir Rintel <lkundrak@v3.sk> - 0.47-0.9.20090518svn
- Update past upstream Beta release

* Mon May 18 2009 Lubomir Rintel <lkundrak@v3.sk> - 0.47-0.8.20090508svn
- Fix ODG export

* Fri May 08 2009 Lubomir Rintel <lkundrak@v3.sk> - 0.47-0.7.20090508svn
- Update to a post-alpha snapshot
- Upstream applied our GCC 4.4 patch

* Fri Apr 10 2009 Lubomir Rintel <lkundrak@v3.sk> - 0.47-0.6.20090410svn
- Update to newer snapshot
- Fix doc/incview reversed subpackage content

* Wed Mar 04 2009 Lubomir Rintel <lkundrak@v3.sk> - 0.47-0.6.20090301svn
- Rebuild for new ImageMagick

* Wed Mar 04 2009 Lubomir Rintel <lkundrak@v3.sk> - 0.47-0.5.20090301svn
- Split documentation and inkview into subpackages

* Mon Mar 02 2009 Lubomir Rintel <lkundrak@v3.sk> - 0.47-0.4.20090301svn
- Bump to later SVN snapshot to fix inkscape/+bug/331864
- Fix a startup crash when compiled with GCC 4.4
- It even runs now! :)

* Fri Feb 27 2009 Lubomir Rintel <lkundrak@v3.sk> - 0.47-0.4.20090227svn
- Enable the test suite

* Fri Feb 27 2009 Lubomir Rintel <lkundrak@v3.sk> - 0.47-0.3.20090227svn
- Past midnight! :)
- More recent snapshot, our gcc44 fixes now upstream
- One more gcc44 fix, it even compiles now
- We install icons now, update icon cache
- Disable inkboard, for it won't currently compile

* Thu Feb 26 2009 Lubomir Rintel <lkundrak@v3.sk> - 0.47-0.3.20090226svn
- Later snapshot
- Compile with GCC 4.4

* Tue Jan 06 2009 Lubomir Rintel <lkundrak@v3.sk> - 0.47-0.3.20090105svn
- Update to newer SVN
- Drop upstreamed patches
- Enable WordPerfect Graphics support
- Enable embedded Perl scripting
- Enable Imagemagick support
- Disable OpenSSL due to licensing issues

* Thu Aug 14 2008 Lubomir Rintel <lkundrak@v3.sk> - 0.47-0.3.20080814svn
- Update to today's SVN snapshot
- Drop the upstreamed poppler patch

* Wed Aug 13 2008 Lubomir Rintel <lkundrak@v3.sk> - 0.47-0.2.20080705svn
- Rediff patches for zero fuzz
- Use uniconvertor to handle CDR and WMF (#458845)

* Wed Jul 09 2008 Lubomir Rintel <lkundrak@v3.sk> - 0.47-0.1.20080705svn
- Subversion snapshot

* Wed Jul 09 2008 Lubomir Rintel <lkundrak@v3.sk> - 0.46-4
- Fix compile issues with newer gtk and poppler

* Thu Jun 26 2008 Lubomir Rintel <lkundrak@v3.sk> - 0.46-3
- Remove useless old hack, that triggered an assert after gtkfilechooser switched to gio

* Fri Apr 11 2008 Lubomir Kundrak <lkundrak@redhat.com> - 0.46-2.1
- More buildrequires more flexible, so that this builds on RHEL

* Sat Apr 05 2008 Lubomir Kundrak <lkundrak@redhat.com> - 0.46-2
- Fix LaTeX rendering, #441017

* Tue Mar 25 2008 Lubomir Kundrak <lkundrak@redhat.com> - 0.46-1
- 0.46 released

* Sun Mar 23 2008 Lubomir Kundrak <lkundrak@redhat.com> - 0.46-0.3.pre3
- Rebuild for newer Poppler

* Wed Mar 12 2008 Lubomir Kundrak <lkundrak@redhat.com> - 0.46-0.2.pre3
- Probably last prerelease?

* Fri Feb 22 2008 Lubomir Kundrak <lkundrak@redhat.com> - 0.46-0.2.pre2
- Panel icon sizes

* Sun Feb 17 2008 Lubomir Kundrak <lkundrak@redhat.com> - 0.46-0.1.pre2
- 0.46pre2
- Dropping upstreamed patches

* Sat Feb 16 2008 Lubomir Kundrak <lkundrak@redhat.com> - 0.45.1+0.46pre1-5
- Attempt to fix the font selector (#432892)

* Thu Feb 14 2008 Lubomir Kundrak <lkundrak@redhat.com> - 0.45.1+0.46pre1-4
- Tolerate recoverable errors in OCAL feeds
- Fix OCAL insecure temporary file usage (#432807)

* Wed Feb 13 2008 Lubomir Kundrak <lkundrak@redhat.com> - 0.45.1+0.46pre1-3
- Fix crash when adding text objects (#432220)

* Thu Feb 07 2008 Lubomir Kundrak <lkundrak@redhat.com> - 0.45.1+0.46pre1-2
- Build with gcc-4.3

* Wed Feb 06 2008 Lubomir Kundrak <lkundrak@redhat.com> - 0.45.1+0.46pre1-1
- 0.46 prerelease
- Minor cosmetic changes to satisfy the QA script
- Dependency on Boost
- Inkboard is not optional
- Merge from Denis Leroy's svn16571 snapshot:
- Require specific gtkmm24-devel versions
- enable-poppler-cairo
- No longer BuildRequire libsigc++20-devel

* Wed Dec  5 2007 Denis Leroy <denis@poolshark.org> - 0.45.1-5
- Rebuild with new openssl

* Sun Dec 02 2007 Lubomir Kundrak <lkundrak@redhat.com> - 0.45.1-4
- Added missing dependencies for modules (#301881)

* Sun Dec 02 2007 Lubomir Kundrak <lkundrak@redhat.com> - 0.45.1-3
- Satisfy desktop-file-validate, so that Rawhide build won't break

* Sat Dec 01 2007 Lubomir Kundrak <lkundrak@redhat.com> - 0.45.1-2
- Use GTK print dialog
- Added compressed SVG association (#245413)
- popt headers went into popt-devel, post Fedora 7
- Fix macro usage in changelog

* Wed Mar 21 2007 Denis Leroy <denis@poolshark.org> - 0.45.1-1
- Update to bugfix release 0.45.1
- Added R to ImageMagick-perl (#231563)

* Wed Feb  7 2007 Denis Leroy <denis@poolshark.org> - 0.45-1
- Update to 0.45
- Enabled inkboard, perl and python extensions
- Added patch for correct python autodetection
- LaTex patch integrated upstreamed, removed
- Some rpmlint cleanups

* Wed Dec  6 2006 Denis Leroy <denis@poolshark.org> - 0.44.1-2
- Added patches to fix LaTex import (#217699)
- Added patch to base postscript import on pstoedit plot-svg

* Thu Sep  7 2006 Denis Leroy <denis@poolshark.org> - 0.44.1-1
- Update to 0.44.1
- Removed png export patch, integrated upstream
- Some updated BRs

* Mon Aug 28 2006 Denis Leroy <denis@poolshark.org> - 0.44-6
- FE6 Rebuild

* Tue Aug 22 2006 Denis Leroy <denis@poolshark.org> - 0.44-5
- Removed skencil Require (bug 203229)

* Thu Aug 10 2006 Denis Leroy <denis@poolshark.org> - 0.44-4
- Added patch to fix png dpi export problem (#168406)

* Wed Aug  9 2006 Denis Leroy <denis@poolshark.org> - 0.44-3
- Bumping up release to fix upgrade path

* Wed Jun 28 2006 Denis Leroy <denis@poolshark.org> - 0.44-2
- Update to 0.44
- Removed obsolete patches
- Disabled experimental perl and python extensions
- Added pstoedit, skencil, gtkspell and LittleCms support
- Inkboard feature disabled pending further security tests

* Tue Feb 28 2006 Denis Leroy <denis@poolshark.org> - 0.43-3
- Rebuild

* Mon Jan 16 2006 Denis Leroy <denis@poolshark.org> - 0.43-2
- Updated GC patch, bug 171791

* Sat Dec 17 2005 Denis Leroy <denis@poolshark.org> - 0.43-1
- Update to 0.43
- Added 2 patches to fix g++ 4.1 compilation issues
- Enabled new jabber/loudmouth-based inkboard feature

* Mon Sep 26 2005 Denis Leroy <denis@poolshark.org> - 0.42.2-2
- rebuilt with newer glibmm

* Thu Sep  1 2005 Michael Schwendt <mschwendt[AT]users.sf.net> - 0.42.2-1
- update to 0.42.2

* Thu Aug 18 2005 Michael Schwendt <mschwendt[AT]users.sf.net> - 0.42-3
- rebuilt
- add patch to repair link-check of GC >= 6.5 (needs pthread and dl)

* Fri Jul 29 2005 Michael Schwendt <mschwendt[AT]users.sf.net> - 0.42-2
- Extend ngettext/dgettext patch for x86_64 build.

* Tue Jul 26 2005 Michael Schwendt <mschwendt[AT]users.sf.net> - 0.42-1
- update to 0.42 (also fixes #160326)
- BR gnome-vfs2-devel
- no files left in %%_libdir/inkscape
- include French manual page
- GCC4 patch obsolete, 64-bit patch obsolete, dgettext patch split off

* Tue May 31 2005 Michael Schwendt <mschwendt[AT]users.sf.net> - 0.41-7
- append another 64-bit related patch (dgettext configure check failed)

* Tue May 31 2005 Michael Schwendt <mschwendt[AT]users.sf.net> - 0.41-6
- remove explicit aclocal/autoconf calls in %%build as they create a
  bad Makefile for FC4/i386, which causes build to fail (#156228),
  and no comment explains where they were added/needed

* Tue May 31 2005 Michael Schwendt <mschwendt[AT]users.sf.net> - 0.41-5
- bump and rebuild as 0.41-4 failed in build system setup

* Wed May 25 2005 Jeremy Katz <katzj@redhat.com> - 0.41-4
- add patch for gcc4 problems (ignacio, #156228)
- fix build on 64bit boxes.  sizeof(int) != sizeof(void*)

* Sun May 22 2005 Jeremy Katz <katzj@redhat.com> - 0.41-3
- rebuild on all arches

* Thu Apr 07 2005 Michael Schwendt <mschwendt[AT]users.sf.net>
- rebuilt

* Wed Feb 09 2005 Phillip Compton <pcompton[AT]proteinmedia.com> - 0.41-1
- 0.41.
- enable python.

* Sat Dec 04 2004 Phillip Compton <pcompton[AT]proteinmedia.com> - 0.40-1
- 0.40.

* Tue Nov 16 2004 Phillip Compton <pcompton[AT]proteinmedia.com> - 0.40-0.pre3
- 0.40pre3.

* Thu Nov 11 2004 Phillip Compton <pcompton[AT]proteinmedia.com> - 0.39-0.fdr.2
- post/postun for new mime system.
- Dropped redundant BR XFree86-devel.

* Sun Aug 29 2004 Phillip Compton <pcompton[AT]proteinmedia.com> - 0:0.39-0.fdr.1
- 0.39.

* Sat Apr 10 2004 P Linnell <scribusdocs at atlantictechsolutions.com> 0:0.38.1-0.fdr.1
- respin real fix for Provides/Requires for perl(SpSVG)

* Fri Apr 9 2004 P Linnell <scribusdocs at atlantictechsolutions.com> 0:0.38.1-0.fdr.0
- respin with updated tarball with fix for postscript printing

* Thu Apr 8 2004 P Linnell <scribusdocs at atlantictechsolutions.com> 0:0.38-0.fdr.2
- respin to fix provides

* Thu Apr 8 2004 P Linnell <scribusdocs at atlantictechsolutions.com> 0:0.38.0.fdr.1
- version upgrade with many improvements and bug fixes

* Fri Mar 19 2004 P Linnell <scribusdocs at atlantictechsolutions.com> 0:0.37.0.fdr.7
- repsin - sourceforge does not allow reloading files with same name
* Tue Mar 16 2004 P Linnell <scribusdocs at atlantictechsolutions.com> 0:0.37.0.fdr.6
- fix typo in provides
* Tue Mar 16 2004 P Linnell <scribusdocs at atlantictechsolutions.com> 0:0.37.0.fdr.5
- add %%{release} to provides perl(SpSVG) = %%{epoch}:%%{version}:%%{release} only
* Tue Mar 16 2004 P Linnell <scribusdocs at atlantictechsolutions.com> 0:0.37.0.fdr.4
- add %%{release} to provides
* Sun Mar 14 2004 P Linnell <scribusdocs at atlantictechsolutions.com> 0:0.37.0.fdr.3
- add arch dependent flags
* Thu Mar 11 2004 P Linnell <scribusdocs at atlantictechsolutions.com> 0:0.37.0.fdr.2
- add libsigc++-devel instead of add libsigc++ - duh
- add BuildRequires:  perl-XML-Parser
- fix package name to follow package naming guidelines
* Mon Mar 1 2004   P Linnell <scribusdocs at atlantictechsolutions.com>   0:0.37.1.fdr.1
- disable static libs
- enable inkjar
* Tue Feb 10  2004 P Linnell <scribusdocs at atlantictechsolutions.com>   0:0.37.0.fdr.1
- pgp'd tarball from inkscape.org
- clean out the cvs tweaks in spec file
- enable gnome-print
- add the new tutorial files
- make sure .mo file gets packaged
- add provides: perlSVG
- submit to Fedora QA
* Sat Feb 7  2004 P Linnell <scribusdocs at atlantictechsolutions.com>
- rebuild of current cvs
- tweaks to build cvs instead of dist tarball
- add inkview
* Sat Dec 20 2003 P Linnell <scribusdocs at atlantictechsolutions.com>
- First crack at Fedora/RH spec file
- nuke gnome print - it won't work (bug is filed already)
