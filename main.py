#!/usr/bin/env python3.6
#-*- coding: utf-8 -*-
#song = "/path/to/file.mp3"
#audio = MP3(song)
#print(audio.info.length)
import sys
import os
import os.path
import time
import re
import random
import pygame
from glob import glob
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QDirIterator, QDir, QFile
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWidgets import QInputDialog, QLineEdit, QFileDialog, QWidget
from tinytag import TinyTag
#from mutagen.mp3 import MP3   #for getting song duration
from gui import Hell_Player

pygame.mixer.init()
mus = pygame.mixer.music
mus.set_volume(0.47)

class Timer(QtCore.QTimer):
	def __init__(self, parent = None):
		super().__init__(parent)
		self.current_timer_test = None
		self.ind = 1
		self.current_position = 0
		self.timer()
		self.current_position = Hell_Player.position * 5
		
	def progress(self):
		if Hell_Player.pause_state == False and Hell_Player.play_state:
			
			
			Hell_Player.progressBar.setValue(self.current_position)
			self.current_position += 1

	def timer(self):	
		if self.current_timer_test:
			self.current_timer_test.stop()
			self.current_timer_test.deleteLater()
		self.current_timer_test = QtCore.QTimer()
		self.current_timer_test.timeout.connect(self.timer)
		self.current_timer_test.setSingleShot(True)
		self.current_timer_test.start(200)
		self.progress()

class MyFirstPlayer(QtWidgets.QWidget, Hell_Player):
	def __init__(self, parent = None):
		super().__init__(parent)
		self.position = 0
		self.setupUi(self)
		self.new_playlist = True
		self.pause_state = False
		self.play_state = False
		self.width = 635
		self.height = 370
		self.playlist_height = 590
		self.playlist = []
		self.test_var = 1
		self.current_timer = None
		self.current_timer_progress_bar = None
#		self.current_position = 0
		self.counter = 0
		self.current_sec = 0
		self.current_min = 0
		
		# Connect buttons with custom functions
		self.playButton.clicked.connect(self.play_button)
		self.pauseButton.clicked.connect(self.pause)
		self.nextButton.clicked.connect(self.next)
		self.prevButton.clicked.connect(self.prev)

		self.open_folder.clicked.connect(self.dir_choosing)
		self.playlistButton.clicked.connect(self.open_playlist)
		self.ShowPL.clicked.connect(self.increase_height)
		self.HidePL.clicked.connect(self.reduce_height)
		self.tableWidget.cellDoubleClicked["int", "int"].connect(self.get_item_clicked)
		self.volumeSlider.valueChanged["int"].connect(self.set_volume)
		self.muteCheckBox.stateChanged["int"].connect(self.mute)
		self.song_min.display("00")
		self.song_sec.display("00")
		self.progressBar.valueChanged["int"].connect(self.repaint)

		self.progressBar.sliderMoved['int'].connect(self.set_position)
		
		self.HidePL.setVisible(False)
		self.pauseButton.setVisible(False)
		self.tableWidget.setColumnWidth(0, 1)
		self.tableWidget.setColumnWidth(1, 237)
		self.tableWidget.setColumnWidth(2, 129)
		self.tableWidget.setColumnWidth(3, 129)
		self.tableWidget.setColumnWidth(4, 51)
		

	def set_position(self, posi):
		if self.check_playlist():
			self.current_sec = int(self.timer_object.current_position / 5) - 1
			while self.current_sec > 60:
				self.current_sec = self.current_sec - 60
			self.current_min = int(self.timer_object.current_position / 300)
			if self.play_state:
				self.position = int(posi / 5)
				mus.pause()
				mus.play(0, self.position)
				self.timer_object.current_position = self.position * 5
				
	def set_volume(self, vol):
		if self.muteCheckBox.isChecked:
			mus.set_volume(vol / 50)
			self.muteCheckBox.setChecked(False)
		else:
			mus.set_volume(vol / 50)

	def mute(self, state):
		if state == 2:   #state 2 = unmute
			self.volume = mus.get_volume()
			mus.set_volume(0)
			self.volumeSlider.setProperty("value", 0)
			self.muteCheckBox.setChecked(True)
		elif state == 0:   #state 0 = mute
			mus.set_volume(self.volume)
			self.volumeSlider.setProperty("value", self.volume * 50)
		
	def get_item_clicked(self, row, column):
		self.pause_state = False
		self.index = row
		self.play_music()
		self.pauseButton.show()
		self.playButton.hide()
		self.timer_object.current_position = 0

	def window_resizing(self):
		width = self.frameGeometry().width()
		height = self.frameGeometry().height()
		print(width, height)
		
	def increase_height(self):
		self.width = self.frameGeometry().width()
		self.height = self.frameGeometry().height()
		self.setMaximumSize(QtCore.QSize(1920, 1080))
		self.setMinimumSize(QtCore.QSize(635, 590))
		self.resize(self.width, self.playlist_height - 28)
	
	def reduce_height(self):
		self.width = self.frameGeometry().width()
		self.height = self.frameGeometry().height()
		self.playlist_height = self.frameGeometry().height()
		self.setMinimumSize(QtCore.QSize(635, 339))
		self.setMaximumSize(QtCore.QSize(1920, 339))
		self.resize(self.width, 339)
	
	def show_hidden_playlist(self):
		self.playlist_frame.setVisible(True)
		self.increase_height()
		
	def dir_choosing(self):
		self.index = 0
		self.new_playlist = True
		directory = QFileDialog.getExistingDirectory(None, "Open Directory", "/", QFileDialog.ShowDirsOnly)
		if directory:
			os.chdir(directory)
			self.tableWidget.setRowCount(0)
			self.playlist = []
			filters = QDir.Files
			nameFilters = ["*.mp3", "*.MP3", "*.Mp3", "*.mP3"]
			qDirIterator = QDirIterator(directory, nameFilters, filters, QDirIterator.Subdirectories)
			while qDirIterator.hasNext():
				qDirIterator.next()
				fileInfo = qDirIterator.fileInfo()
				fdir = fileInfo.absoluteDir().absolutePath()
				song = qDirIterator.filePath()
				self.playlist.append(song)
				try:
					song_tags = TinyTag.get(song)
				except:
					print("Corrupted file:\n", len(self.playlist),
						  song, "\nCan't get the tags")
					self.add_corrupted_files(song)
				else:
					self.add_items_to_list(song_tags, song)
			self.playlist_action()

	def open_playlist(self):
		self.index = 0
		self.new_playlist = True
		fileName = QFileDialog.getOpenFileName(
					None, "Open Playlist (m3u, pls)",
					"/")[0]
		if fileName:
			self.tableWidget.setRowCount(0)
			self.playlist = []
			playlist_file = open(fileName, "r")
			for items in playlist_file:
				#Removing \n symbols from the end of the file names
				#Making .pls and .m3u playlist files playable
				items = "/" + (items.rpartition("///")[2])[:-1]
				items = re.sub("%20", " ", items)
				if os.path.isfile(items):
					self.playlist.append(items)
					try:
						song_tags = TinyTag.get(items)
					except:
						print("Corrupted file:", items, "\nCan't get the tags")
						self.add_corrupted_files(items)
					else:
						self.add_items_to_list(song_tags, items)
			playlist_file.close()
			self.playlist_action()
		
	def playlist_action(self):
		self.show_hidden_playlist()
		self.HidePL.show()
		self.ShowPL.hide()
		self.song_info_displaying()
		self.playlist_len_for_random = len(self.playlist) - 1
		self.timer_object = Timer()
		
	def add_corrupted_files(self, name):
		self.rowPosition = self.tableWidget.rowCount()
		self.tableWidget.insertRow(self.rowPosition)
		self.tableWidget.setRowHeight(self.rowPosition, 18)
		song_title = name.split("/")[-1]
#		song_title = song_title[-1]
		self.tableWidget.setItem(self.rowPosition, 1,
				QtWidgets.QTableWidgetItem(song_title))		
	
	#add songs to table widget
	def add_items_to_list(self, song_info, file_name):
		self.rowPosition = self.tableWidget.rowCount()
		self.tableWidget.insertRow(self.rowPosition)
		self.tableWidget.setRowHeight(self.rowPosition, 18)
		
		song_title = song_info.title
		try:
			song_title = song_title.encode("latin-1").decode("cp1251")
		except:
			song_title = song_info.title
		if song_title == "":
			song_title = file_name.split("/")[-1]

		song_artist = song_info.artist
		try:
			song_artist = song_artist.encode("latin-1").decode("cp1251")
		except:
			song_artist = song_info.artist
			
		song_album = song_info.album
		try:
			song_album = song_album.encode("latin-1").decode("cp1251")
		except:
			song_album = song_info.album
			
		song_year = song_info.year

		#tooltip = song_title + "::" + song_artist + "::" + song_album + "::" + song_year
		#self.tableWidget.setToolTip(tooltip)
		self.tableWidget.setItem(self.rowPosition, 1, QtWidgets.QTableWidgetItem(song_title))
		self.tableWidget.setItem(self.rowPosition, 2, QtWidgets.QTableWidgetItem(song_artist))
		self.tableWidget.setItem(self.rowPosition, 3, QtWidgets.QTableWidgetItem(song_album))
		self.tableWidget.setItem(self.rowPosition, 4, QtWidgets.QTableWidgetItem(song_year))
		
	#Displays currently played song title
	def song_info_displaying(self):
		self.song_title_field.clear()
		current_song = self.playlist[self.index]
		current_display_info = TinyTag.get(current_song)
		title = str(current_display_info.title)
		try:
			title = title.encode("latin-1").decode("cp1251")
		except:
			title = str(current_display_info.title)

		album = str(current_display_info.album)
		try:
			album = album.encode("latin-1").decode("cp1251")
		except:
			album = str(current_display_info.album)
			
		artist = str(current_display_info.artist)
		try:
			artist = artist.encode("latin-1").decode("cp1251")
		except:
			artist = str(current_display_info.artist)
			
		year = str(current_display_info.year)
		if year == "None":
			album_to_display = album
		else:
			album_to_display = album + " (" + year + ")"
		self.song_title_field.setText(title)
		self.album_name_field.setText(album_to_display)
		self.artist_name_field.setText(artist)
		self.tableWidget.selectRow(self.index)

	#To check whether playlist is empty or not	
	def check_playlist(self):
		if len(self.playlist) == 0:
			self.song_title_field.clear()
			self.song_title_field.setText("Playlist is empty!")
			self.pauseButton.setVisible(False)
			self.playButton.setVisible(True)
			check = False
		else:
			check = True
		return check

	#After clicking Play button checks: playlist for items, shuffle status.
	def play_button(self):
		if self.check_playlist():
			if (self.play_state == False 
					and self.shuffle_box.isChecked() 
					and self.new_playlist):
				self.index_generate()
				self.play_music()
			else:
				self.play_music()

	
	def play_music(self):
		if self.pause_state == False:
			self.current_sec = 0
			self.current_min = 0
			self.song_sec.display("00")
			self.song_min.display("00")
			
		current = TinyTag.get(self.playlist[self.index])
		self.duration = int(current.duration * 5)
#		print(self.duration)
#			current = MP3(self.playlist[self.index])
#			self.duration = int(current.info.length) * 5
		self.progressBar.setMaximum(self.duration)
			
		self.play_state = True
		self.new_playlist = False

		if self.check_playlist():
			song = self.playlist[self.index]
			if self.pause_state:
				self.pause_state = False
				mus.unpause()
			else:
				try:
					self.song_info_displaying()
					mus.load(song)
					mus.play()
					self.wait_for_end()
				except:
					print("Kernel panic! Can't open the file!")
					self.index += 1
					self.play_music()
					self.wait_for_end()
				else:
					self.song_info_displaying()
					mus.load(song)
					mus.play()
					self.wait_for_end()
	
	def time_calculating_crazy_method(self):
		if self.current_sec < 10 and self.current_min == 0:
			self.song_sec.display("0" + str(self.current_sec))
		elif self.current_sec < 10 and (0 < self.current_min < 10):
			self.song_min.display("0" + str(self.current_min))
			self.song_sec.display("0" + str(self.current_sec))
		elif self.current_sec < 10 and self.current_min >= 10:
			self.song_min.display(str(self.current_min))
			self.song_sec.display("0" + str(self.current_sec))
		elif (10 <= self.current_sec < 60) and self.current_min == 0:
			self.song_sec.display(str(self.current_sec))
		elif (10 <= self.current_sec < 60) and (0 < self.current_min < 10):
			self.song_min.display("0" + str(self.current_min))
			self.song_sec.display(str(self.current_sec))
		elif (10 <= self.current_sec < 60) and self.current_min >= 10:
			self.song_min.display(str(self.current_min))
			self.song_sec.display(str(self.current_sec))

	def time_display(self):
		if self.current_sec < 60:
			self.time_calculating_crazy_method()
			self.current_sec += 1
		else:
			self.current_min += 1
			self.current_sec = 0
			self.time_calculating_crazy_method()
			self.current_sec += 1


	def time_display_test(self):
		minutes = int(self.counter / 60)
		seconds = self.counter - (60 * minutes)
		print (minutes, seconds)


	#Check playing status
	def wait_for_end(self):
		pygame.display.init()
		SONG_END = pygame.USEREVENT + 1
		mus.set_endevent(SONG_END)	
		for event in pygame.event.get():
#			if event.type != SONG_END:
#				self.wait_for_end()
			if event.type == SONG_END:
				pygame.display.quit()
				self.next()
#		self.tableWidget.selectRow(self.index)
		self.start_timer()

					
	#Loop repeat method
	def start_timer(self):
		if self.current_timer:
			if self.pause_state == False and self.play_state:
				self.time_display()
			self.current_timer.stop()
			self.current_timer.deleteLater()
		self.current_timer = QtCore.QTimer()
		self.current_timer.timeout.connect(self.wait_for_end)
		self.current_timer.setSingleShot(True)
		self.current_timer.start(1000)
		self.counter += 1

			
	#Generating index for next song in playlist
	def index_generate(self):
		if self.shuffle_box.isChecked():
			index_next = random.randint(0, self.playlist_len_for_random)
			if index_next == self.index:
				self.index_generate()
			else:
				self.index = index_next
		else:
			if self.index >= self.playlist_len_for_random:
				self.index = 0
			else:
				self.index += 1
		
	def next(self):
		if self.check_playlist():
			if (self.new_playlist and self.play_state and
					self.shuffle_box.isChecked() == False):
				self.index = 0
				self.play_music()
			else:
				self.index_generate()
				self.song_change()
			
	def prev(self):
		if self.check_playlist():
			if self.index > 0:
				self.index_generate()
				self.index -= 2
				self.song_change()
			else:
				self.index_generate()
				self.index -= 1
				self.song_change()
	
	def song_change(self):
		self.counter = 0
		self.current_sec = 0
		self.current_min = 0
		self.song_sec.display("00")
		self.song_min.display("00")
		self.progressBar.setValue(0)
		if self.pause_state == False:
			if self.play_state == False:
				self.song_info_displaying()
			else:
				self.position = 0
				self.play_music()
		else:
			mus.stop()
			self.song_info_displaying()
			self.pause_state = False
			self.play_state = False
			self.playButton.show()
			self.pauseButton.hide()
		self.new_playlist = False
		self.timer_object.current_position = 0
				
	def pause(self):
		mus.pause()
		self.pause_state = True

if __name__ == '__main__':
	app = QtWidgets.QApplication(sys.argv)
	Hell_Player = MyFirstPlayer()
	Hell_Player.show()
	sys.exit(app.exec_())

