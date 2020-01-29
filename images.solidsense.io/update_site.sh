#!/bin/sh

# global variables
REPOS=" \
	github.com/SolidRun/SolidSense-V1.git;branch=V0.951;protocol=https:/var/www/images.solidsense.io/.git/SolidSense-V1 \
"

DIR_MAPPINGS=" \
	SolidSense-V1:doc:/var/www/images.solidsense.io/html/SolidSense/doc \
	SolidSense-V1:custom:/var/www/images.solidsense.io/html/SolidSense/config \
"

#functions
find_value () {
	string="${1}"
	search="${2}"

	value="$(echo "${string}" | \
		awk -v SEARCH="${search}" \
		'BEGIN {
				OLD_FS = FS
				FS = ";"
		}
		{
			for ( i = 1; i <= NF; i++)
			{
				if ($i ~ SEARCH)
				{
					FS = "="
					$0 = $i
					print $2
					FS = OLD_FS
				}
			}
		}'
	)"

	echo "${value}"
}

handle_linking () {
	srcdir="${1}"

	for entry in ${DIR_MAPPINGS}; do
		repo_name="$(echo "${entry}" | \
			awk 'BEGIN {
				FS = ":"
			}
			{
				print $1
			}'
		)"
		repo_subdir="$(echo "${entry}" | \
			awk 'BEGIN {
				FS = ":"
			}
			{
				print $2
			}'
		)"
		dstdir="$(echo "${entry}" | \
			awk 'BEGIN {
				FS = ":"
			}
			{
				print $3
			}'
		)"
		if [ "${repo_name}" = "$(basename "${srcdir}")" ]; then
			if [ ! -d "${dstdir}" ]; then
				mkdir -p "${dstdir}"
			fi
			for file in "${srcdir}"/"${repo_subdir}"/*; do
				srcfile="${file}"
				dstfile="${dstdir}/$(basename "${file}")"
				if [ ! -f "${dstfile}" ]; then
					ln "${srcfile}" "${dstfile}"
				fi
			done
			for file in "${dstdir}"/*; do
				srcfile="${srcdir}/${repo_subdir}/$(basename "${file}")"
				if [ ! -f "${srcfile}" ] && [ "${srcfile}" != "index.html" ]; then
					echo "Deleting file: ${file}"
					rm "${file}"
				fi
			done
		fi
	done
}

handle_repo () {
	for entry in ${REPOS}; do
		repo_tmp="$(echo "${entry}" | \
			awk 'BEGIN {
				FS = ":"
			}
			{
				print $1
			}'
		)"
		repo="$(echo "${repo_tmp}" | \
			awk 'BEGIN {
				FS = ";"
			}
			{
				print $1
			}'
		)"
		branch="$(find_value "${repo_tmp}" "branch")"
		protocol="$(find_value "${repo_tmp}" "protocol")"
		destdir="$(echo "${entry}" | \
			awk 'BEGIN {
				FS = ":"
			}
			{
				print $2
			}'
		)"

		# Update or clone repo
		if [ -d "${destdir}" ] ; then
			cd "${destdir}" && git pull
		else
			mkdir -p "${destdir}"
			git_url="${protocol}://${repo}"
			if [ -z "${branch}" ]; then
				git clone "${git_url}" "${destdir}"
			else
				git clone --single-branch --branch "${branch}" "${git_url}" "${destdir}"
			fi
		fi

		# Update links
		handle_linking "${destdir}"
	done
}

# main

handle_repo
