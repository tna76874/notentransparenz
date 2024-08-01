#!/bin/bash

mike list -b gh-pages

read -p "Welche Version soll gelöscht werden? " version

# Führe den Befehl 'mike delete VERSION -b gh-pages' aus
mike delete "$version" -b gh-pages --push
