#!/usr/bin/env python3

###############################
#
#	IT IS A PROTOTYPE 
#	DON'T USE IN PRODUCTION
#	-----------------------
#	FOR STUDY ONLY
#
###############################


import os
import sys
import io
from bitstring import ConstBitStream, BitArray, ReadError
import wave


IA_ELEMENT_NAMES = {
	8 : "IAFrame: Frame Header",              # 0x08
	16 : "Bed Definition",                    # 0x10
	32 : "Bed Remap",                         # 0x20
	64 : "Object Definition",                 # 0x40
	128 : "Extended Object Zone Definition",  # 0x80
	256 : "Authoring Tool Information",       # 0x100
	257 : "User Defined Data",                # 0x101
	512 : "Audio Data DLC Encoded",           # 0x200
	1024 : "Audio Data PCM",                  # 0x400
}
IA_ELEMENT_PARSERS = {
	   8 : "iaframe_parser", 
	  16 : "bed_definition_parser",
	  32 : "bed_remap_parser",				  # bed remap
	  64 : "object_definition_parser",
	 128 : "unknown_parser",
	 256 : "authoring_parser",
	 257 : "user_defined_data_parser",
	 512 : "audio_data_dlc_parser",
	1024 : "audio_data_pcm_parser",
}
SAMPLERATES = {
	0 : 48000,
	1 : 96000,
	2 : None,
	3 : None,
}
BITDEPTHS = {
	0 : 16,
	1 : 24,
	2 : None,
	3 : None,
}
FRAMERATES = {
	0: 24,
	1: 25,
	2: 30,
	3: 48,
	4: 50,
	5: 60,
	6: 96,
	7: 100,
	8: 120,
	9: 23.976,  # maybe... could be wrong
}
# Hz { FrameRateCode : SampleCount }
SAMPLECOUNTS = {
	48000: {
		24: 2000,
		25: 1920,
		30: 1600,
		48: 1000,
		50: 960,
		60: 800,
		96: 500,
		100: 480,
		120: 400,
		23.976 : 2000,  # maybe... could be wrong
	},
	96000: {
		24: 4000,
		25: 3840,
		30: 3200,
		48: 2000,
		50: 1920,
		60: 1600,
		96: 1000,
		100: 960,
		120: 800,
		23.976 : 4000,  # maybe... could be wrong
	}
}
USECASES = {
	1: "5.1 (SMPTE ST-428-12)",
	2: "7.1DS (SMPTE ST-428-12)",
	3: "7.1SDS (SMPTE ST-428-12)",
	4: "11.1HT (SMPTE ST 2098-5)",
	5: "13.1HT (SMPTE ST 2098-5)",
	6: "9.1OH (SMPTE ST 2098-5)",
	255: "Always use",
}


# ---- IAB + ATMOS -----
SUB_BLOCK_NUMS = {
	48000: {
		24: 10,
		25: 10,
		30: 8,
		48: 5,
		50: 5,
		60: 4,
		96: 5,
		100: 4,
		120: 4,
	},
	96000: {
		24: 10,
		25: 10,
		30: 8,
		48: 5,
		50: 5,
		60: 4,
		96: 5,
		100: 4,
		120: 4,
	}
}
SUB_BLOCK_SIZES = {
	48000: {
		24  : 200,
		25  : 192,
		30  : 200,
		48  : 200,
		50  : 192,
		60  : 200,
		96  : 100,
		100 : 120,
		120 : 100,
	},
	96000: {
		24  : 400,
		25  : 384,
		30  : 400,
		48  : 400,
		50  : 384,
		60  : 400,
		96  : 200,
		100 : 240,
		120 : 200,
	}
}

CHANNEL_NAMES = {
	"0x0" : "Left",
	"0x1" : "Left Center",
	"0x2" : "Center",
	"0x3" : "Right Center",
	"0x4" : "Right",
	"0x5" : "Left Side Surround",
	"0x6" : "Left Surround",
	"0x7" : "Left Rear Surround",
	"0x8" : "Right Rear Surround",
	"0x9" : "Right Side Surround",
	"0xa" : "Right Surround",
	"0xb" : "Left Top Surround",
	"0xc" : "Right Top Surround",
	"0xd" : "LFE",
	"0xe" : "Left Height",
	"0xf" : "Right Height",
	"0x10": "Center Height",
	"0x11": "Left Surround Height",
	"0x12": "Right Surround Height",
	"0x13": "Left Side Surround Height",
	"0x14": "Right Side Surround Height",
	"0x15": "Left Rear Surround Height",
	"0x16": "Right Rear Surround Height",
	"0x17": "Top Surround",
}

ZONE_DEFINITION_NAMES = {
	0: "All screen speakers left of center",
	1: "Screen center speakers",
	2: "All screen speakers right of center",
	3: "All speakers on left wall",
	4: "All speakers on right wall",
	5: "All speakers on left half of rear wall",
	6: "All speakers on right half of rear wall",
	7: "All overhead speakers left of center",
	8: "All overhead speakers right of center"
}

DECORRELATION_COEF_PREFIX_NAMES = {
	0 : "No decorrelation",
	1 : "Maximum decorrelation",
	2 : "Decorrelation coefficient follows in the bitstream",
	3 : "Reserved"
}
GAIN_PREFIX_NAMES = {
	0: "Set gain to 1.0",
	1: "Set gain to 0.0",
	2: "Gain Code follows in the bitstream. Set gain based on Gain Code",
	3: "Reserved"
}
AUDIO_DESCRIPTION_NAMES = {
	0: "No AudioDescription",
	1: "Not Indicated",
	2: "Dialog",
	4: "Music",
	8: "Effects",
	16: "Foley",
	32: "Ambience",
	64: "Reserved",
	128: "Additional Information text string",
}



"""
	===================
	   Display Class
	===================
"""
PRINT_LEVEL_TAB = 0 
class pprint(object):
	def __init__(self):
		global PRINT_LEVEL_TAB
		PRINT_LEVEL_TAB += 1
		self.PRINT_LEVEL_TAB = PRINT_LEVEL_TAB
		# print("%s" % (("   %s" % '│') * (self.PRINT_LEVEL_TAB-1)))
		self.print("─"*100, lt='', sep='┌')
	def __del__(self):
		self.print("%s" % ("─"*100), lt='', sep='└')
		print("%s" % (("     %s" % '│') * (self.PRINT_LEVEL_TAB-1)))
		global PRINT_LEVEL_TAB
		PRINT_LEVEL_TAB -= 1
	def print(self, string, ft="", lt="      ", sep='│', end='\n'):
		print("%s%s%s%s" % (("     %s" % sep) * (self.PRINT_LEVEL_TAB), ft, lt, string), end=end)
	def title(self, string):
		l = len(string)
		self.print("\033[3%sm───── %s %s\033[0m  \033[4;30m[%s]\033[0m" % (self.PRINT_LEVEL_TAB, string, ('─'* (80 - l)), self.PRINT_LEVEL_TAB), lt='')
	def main(self, string):
		l = len(string)
		self.print("\033[32m▐━━━━ %s %s▐\033[0m  \033[4;30m[%s]\033[0m" % (string, ('━' * (80 - l)), self.PRINT_LEVEL_TAB), lt='')
	

"""
	=====================
		Plex Coding
	=====================
	5.2 Plex encoding
	Plex(n) defines a field size of n bits that may be expanded 
	if it is insufficient to hold the desired symbol.
	=====================
	TODO: merge plex8 + plex4
"""
def plex8(bitstream):
	buffer = bitstream.read("bits:8")
	if buffer.uint == 255:
		buffer = bitstream.read("bits:16")
		if buffer.uint == 65535:
			buffer = bitstream.read("bits:32")
	return buffer

def plex4(bitstream):
	buffer = bitstream.read("bits:4")
	if buffer.uint == 15:
		buffer = bitstream.read("bits:8")
		if buffer.uint == 255:
			buffer = bitstream.read("bits:16")
			if buffer.uint == 65535:
				buffer = bitstream.read("bits:32")
	return buffer


"""
	=============================
		IAElement : IAFrame
	=============================
"""

def iaframe_parser(bytes, **kwargs):

	b = ConstBitStream(bytes)
	p = pprint()
	p.main("IAFrame")

	# IAVersion
	IAFrameVersion = b.read("bits:8")
	p.print("IAVersion : %s" % IAFrameVersion.uint)

	# SampleRate
	SampleRate = b.read("bits:2")
	p.print("SampleRate : %s (%s Hz)" % (SampleRate, SAMPLERATES.get(SampleRate.uint)))

	# BitDepth
	BitDepth = b.read("bits:2")
	p.print("BitDepth : %s (%s bits)" % (BitDepth, BITDEPTHS.get(BitDepth.uint)))

	# FrameRate
	FrameRate = b.read("bits:4")
	p.print("FrameRate : %s (%s fps)" % (FrameRate, FRAMERATES.get(FrameRate.uint)))

	# MaxRendered
	MaxRendered = plex8(b)
	p.print("MaxRendered : %s (%d bytes)" % (MaxRendered, MaxRendered.uint))

	# AlignBits
	p.print("AlignBits(%d)" % b.bytealign())

	# SubElements
	SubElementCount = plex8(b)
	p.print("SubElementCount : %s (%d elements)" % (SubElementCount, SubElementCount.uint))

	for i in range(SubElementCount.uint):

		p1 = pprint()
		p1.title("SubElement %d" % i)

		# ElementID
		ElementID = plex8(b)
		p1.print("SubElementID : %s (%s)" % (ElementID, IA_ELEMENT_NAMES.get(ElementID.uint, "Unknown Element")))
		
		# ElementSize
		ElementSizeBytes = plex8(b)
		p1.print("SubElementSize : %s (%d bytes)" % (ElementSizeBytes, ElementSizeBytes.uint))

		# ElementValue
		ElementValue = b.read("bytes:%d" % ElementSizeBytes.uint)
		p1.print("SubElementValue : %s(..) (%d bytes)" % (ElementValue[0:32].hex(), len(ElementValue)))

		# Bypass Parser
		if FILTER is not None and FILTER not in IA_ELEMENT_NAMES.get(ElementID.uint, "Unknown Element"):
			continue

		# Execute
		funcname = IA_ELEMENT_PARSERS.get(ElementID.uint, 'unknown_parser')
		try:
			globals()[funcname](
				bytes      = ElementValue,
				SampleRate = SAMPLERATES.get(SampleRate.uint),
				BitDepth   = BITDEPTHS.get(BitDepth.uint),
				FrameRate  = FRAMERATES.get(FrameRate.uint),
			)
		except Exception as error:
			p1.print(f"fatal error ({funcname}) : {error}")

		del p1

"""
	=============================
		IAElement : Bed Definition
	=============================
"""
def bed_definition_parser(bytes, **kwargs):

	b = ConstBitStream(bytes)
	p = pprint()
	p.main("Bed Definition")

	if DEBUG:
		p.print("Buffer = hex(%s)" % ConstBitStream(bytes).hex)
		p.print("Buffer = bin(%s)" % ConstBitStream(bytes).bin)
		p.print("Args   = %s"      % kwargs)

	# ------- MetaID ---------------------------------------------
	MetaID = plex8(b)
	p.print("MetaID : %d" % MetaID.uint)

	# -------- ConditionalBed -------------------------------------
	ConditionalBed = b.read("bits:1")
	p.print("ConditionalBed : %s (%s)" % (ConditionalBed, bool(ConditionalBed.uint)))
	if bool(ConditionalBed.uint):
		p.print("Reserved : %s" % b.read("bits:1"))
		BedUseCase = b.read("bits:8")
		p.print("BedUseCase : %s (%s)" % (BedUseCase, USECASES.get(BedUseCase.uint)))

	# -------- ChannelCount ----------------------------------
	ChannelCount = plex4(b)
	p.print("ChannelCount : %d channels" % ChannelCount.uint)


	# -------- Channels --------------------------------------
	for i in range(0, ChannelCount.uint):

		p1 = pprint()
		p1.title("Channel #%d ──────── (%d bits of %d bits)" % (i, b.pos, len(bytes)*8))

		# --- Channel ID (plex4) ------------------
		ChannelID = plex4(b)
		p1.print("ChannelID   : %s - %s" % (str(ChannelID), CHANNEL_NAMES.get(str(ChannelID), "Unknown")))

		# --- AudioDataID (plex8) ----------------
		AudioID = plex8(b)
		p1.print("AudioDataID : %d" % AudioID.uint)

		# --- ChannelGainPrefix -----------------
		ChannelGainPrefix = b.read("bits:2")
		p1.print("ChannelGainPrefix : %s" % bool(ChannelGainPrefix.uint))

		if ChannelGainPrefix.uint > 1:
			ChannelGain = b.read("bits:10")
			p1.print("ChannelGain : %s (%s)" % (ChannelGain, GAIN_PREFIX_NAMES.get(ChannelGain.uint)))

		# ----- ChannelDecorInfo -------
		ChannelDecorInfoExists = b.read("bits:1")
		p1.print("ChannelDecorInfoExists : %s" % bool(ChannelDecorInfoExists.uint))

		if ChannelDecorInfoExists.uint == 1:
			Reserved = b.read("bits:4")
			p1.print("Reserved : %s" % Reserved)

			# ---- ChannelDecorCoef -----
			ChannelDecorCoefPrefix = b.read("bits:2")
			p1.print("ChannelDecorCoefPrefix = %s" % ChannelDecorCoefPrefix)

			if ChannelDecorCoefPrefix.uint > 1:
				ChannelDecorCoef = b.read("bits:8")
				p1.print("ChannelDecorCoef = %s" % ChannelDecorCoef)

		del p1


	# ------- Reerved -----------------------------------------------
	p.print("Reserved : %s (0x180)" % b.read("bits:10"))


	# ------- AlignBits ---------------------------------------------
	p.print("AlignBits(%d)" % b.bytealign())


	# ------- AudioDescription --------------------------------------
	AudioDescription = b.read("bits:8")

	# some AudioDescription code is bigger than 0x80 (128)
	AudioDescriptionCode = AudioDescription.uint
	if AudioDescription.uint >= 128:
		AudioDescriptionCode = (AudioDescription.uint & 128)

	# TODO : FIX THIS, it's a bitmask, not a code
	p.print("AudioDescription : %s (%s, %s) : %s" % (AudioDescription, AudioDescription.uint, AudioDescription.uint & 128, AUDIO_DESCRIPTION_NAMES.get(AudioDescriptionCode)))
	if AudioDescription.uint & 128:  # ascii is only on 7 bits (10000000)
		while True:
			AudioDescriptionText = b.read("bits:8")
			if not AudioDescriptionText:
				break
			p.print("AudioDescriptionText : %s" % AudioDescriptionText, "(%c)" % AudioDescriptionText.uint)


	# ------- SubElements -------------------------------------------
	SubElementCount = plex8(b)
	p.print("SubElementCount : %s (%d)" % (SubElementCount, SubElementCount.uint))

	# Read each SubElements
	for i in range(0, SubElementCount.uint):

		ElementID = b.read("bits:8")
		if not ElementID:
			continue

		p1 = pprint()
		p1.print("SubElementID %d : %s (%s)" % (i, ElementID, IA_ELEMENT_NAMES.get(ElementID.uint)))

		ElementSizeBytes = b.read("bits:8").uint
		p1.print("SubElementSize %d : %d bytes" % (i, ElementSizeBytes))
		ElementValue = b.read("bytes:%d" % ElementSizeBytes)
		p1.print("SubElementValue %s" % ElementValue.hex())

		# Execute
		funcname = IA_ELEMENT_PARSERS.get(ElementID.uint, 'unknown_parser')
		try:
			globals()[funcname](
				bytes      = ElementValue,
				SampleRate = kwargs.get("SampleRate"),
				BitDepth   = kwargs.get("BitDepth"),
				FrameRate  = kwargs.get("FrameRate"),
			)
		except Exception as error:
			p1.print(f"fatal error ({funcname}) : {error}")

		del p1




"""
	========================================
		  IAElement : Object Definition
	========================================
"""
def object_definition_parser(bytes, **kwargs):

	OBJECT_SPREAD_LOWREZ = 0  # Equal spreading in each dimension using 8-bit coding
	OBJECT_SPREAD_NONE   = 1  # Point source (no ObjectSpread value is sent)
	OBJECT_SPREAD_1D     = 2  # Equal spreading in each dimension using 12-bit coding
	OBJECT_SPREAD_3D     = 3  # Specified spreading in each dimension
	MAX_KNOWN_ZONES = 9

	b = ConstBitStream(bytes)
	p = pprint()
	p.main("Object Definition")

	if DEBUG:
		p.print("Buffer = hex(%s)" % ConstBitStream(bytes).hex)
		p.print("Buffer = bin(%s)" % ConstBitStream(bytes).bin)
		p.print("Args   = %s"      % kwargs)

	# -------- Meta ID --------------------------------------------
	MetaID = plex8(b)
	p.print("MetaID : %d" % MetaID.uint)

	# --------- Audio Data ID -------------------------------------
	AudioDataID = plex8(b)
	p.print("AudioDataID : %d" % AudioDataID.uint)

	# -------- ConditionalBed -------------------------------------
	ConditionalObject = b.read("bits:1")
	p.print("ConditionalObject : %s" % ConditionalObject)
	if bool(ConditionalObject.uint):
		p.print("Reserved : %s" % b.read("bits:1"))
		ObjectUseCase = b.read("bits:8")
		p.print("ObjectUseCase : %s (%s)" % (ObjectUseCase, USECASES.get(ObjectUseCase.uint)))


	# --------- Reserved -------------------------------------------
	p.print("Reserved : %s" % b.read("bits:1"))


	# TODO Create NumPanSubBlocksList
	NumPanSubBlocks = 8   # SMPTE.RDD.0029-2019 - Dolby Atmos Bitstream Specification, Table 7
	for i in range(0, NumPanSubBlocks):

		p1 = pprint()
		p1.title("PanSubBlocks #%d ──────── (%d bits of %d bits)" % (i, b.pos, len(bytes)*8))

		if i == 0:
			PanInfoExists = True

		if i > 0:
			PanInfoExists = b.read("bits:1")
			p1.print("PanInfoExists %s (%s)" % (PanInfoExists, bool(PanInfoExists)))

		if bool(PanInfoExists):


			# --------- ObjectGain ----------------------------------------------------------
			ObjectGainPrefix = b.read("bits:2")
			p1.print("ObjectGainPrefix : %s (%s)" % (ObjectGainPrefix, ObjectGainPrefix.uint))
			if ObjectGainPrefix.uint > 1:
				p1.print("ObjectGain : %s" % b.read("bits:10"))
			Reserved = b.read("bits:3")
			p1.print("Reserved : %s" % Reserved)

			# --------- ObjectPosition ------------------------------------------------------
			p1.print("ObjectPosX : %s" % b.read("bits:16"))
			p1.print("ObjectPosY : %s" % b.read("bits:16"))
			p1.print("ObjectPosZ : %s" % b.read("bits:16"))

			# --------- ObjectSnap ----------------------------------------------------------
			ObjectSnap = b.read("bits:1")
			p1.print("ObjectSnap : %s (%s)" % (ObjectSnap, ObjectSnap.uint))
			if bool(ObjectSnap.uint):
				ObjectSnapTolExists = b.read("bits:1")
				p1.print("ObjectSnapTolExists : %s (%s)" % (ObjectSnapTolExists, ObjectSnapTolExists.uint))
				if bool(ObjectSnapTolExists.uint):
					ObjectSnapTolerance = b.read("bits:12")
					p1.print("ObjectSnapTolerance : %s" % ObjectSnapTolerance)
				Res2 = b.read("bits:1")
				p1.print("Res2 = %s" % Res2)


			# ------- ObjectZoneControl ------------------------------------------------------
			ObjectZoneControl = b.read("bits:1")
			p1.print("ObjectZoneControl : %s (%s)" % (ObjectZoneControl, ObjectZoneControl.uint))
			if bool(ObjectZoneControl.uint):
				for i in range(0, 9):
					p2 = pprint()
					p2.print("Zone Definition for %s" % ZONE_DEFINITION_NAMES.get(i))
					ZoneGainPrefix = b.read("bits:2")
					p2.print("ZoneGainPrefix : %s" % ZoneGainPrefix)
					if ZoneGainPrefix.uint > 1:
						ZoneGain = b.read("bits:10")
						p2.print("ZoneGain: %s" % ZoneGain)
					del p2

			# ------ ObjectSpreadMode -------------------------------------------------------
			ObjectSpreadMode = b.read("bits:2")
			p1.print("ObjectSpreadMode : %s (%s)" % (ObjectSpreadMode, ObjectSpreadMode.uint))
			ObjectSpread = 0
			# OBJECT_SPREAD_LOWREZ
			if ObjectSpreadMode.uint == 0:
				ObjectSpread = b.read("bits:8")
			# OBJECT_SPREAD_1D
			if ObjectSpreadMode.uint == 2:
				ObjectSpread = b.read("bits:12")
			# OBJECT_SPREAD_3D
			if ObjectSpreadMode.uint == 3:
				ObjectSpreadX = b.read("bits:12")
				ObjectSpreadY = b.read("bits:12")
				ObjectSpreadZ = b.read("bits:12")
				ObjectSpread = "%s,%s,%s" % (ObjectSpreadX, ObjectSpreadY, ObjectSpreadZ)

			# DistanceXY = Dn/2(n-1) – (2(n-1)-1)/2(n-1), 2n-1-1 <= Dn <= (2n) – 1 
			# DistanceZ = Dn/(2n – 1), 0 <= Dn <= (2n) – 1
			p1.print("ObjectSpread (Distance Coding) = %s" % ObjectSpread)

			# --------- Reserved --------------------------------------------------------------
			p1.print("Reserved : %s" % b.read("bits:4"))


			# --------- ObjectDecorCoef -------------------------------------------------------
			ObjectDecorCoefPrefix = b.read("bits:2")
			p1.print("ObjectDecorCoefPrefix : %s (%s, %s)" % (ObjectDecorCoefPrefix, ObjectDecorCoefPrefix.uint, DECORRELATION_COEF_PREFIX_NAMES.get(ObjectDecorCoefPrefix.uint)))
			if ObjectDecorCoefPrefix.uint > 1:
				ObjectDecorCoef = b.read("bits:8")
				p1.print("ObjectDecorCoef : %s" % ObjectDecorCoef)

		del p1


	# ------- AlignBits ---------------------------------------------
	p.print("AlignBits(%d)" % b.bytealign())


	# ------- AudioDescription --------------------------------------
	AudioDescription = b.read("bits:8")

	# some AudioDescription code is bigger than 0x80 (128)
	AudioDescriptionCode = AudioDescription.uint
	if AudioDescription.uint >= 128:
		AudioDescriptionCode = (AudioDescription.uint & 128)

	# TODO : FIX THIS, it's a bitmask, not a code
	p.print("AudioDescription : %s (%s, %s) : %s" % (AudioDescription, AudioDescription.uint, AudioDescription.uint & 128, AUDIO_DESCRIPTION_NAMES.get(AudioDescriptionCode)))
	if AudioDescription.uint & 128:  # ascii is only on 7 bits (10000000)
		while True:
			AudioDescriptionText = b.read("bits:8")
			if not AudioDescriptionText:
				break
			p.print("AudioDescriptionText : %s" % AudioDescriptionText, "(%c)" % AudioDescriptionText.uint)


	# ------- SubElements -------------------------------------------
	SubElementCount = plex8(b)
	p.print("SubElementCount : %s (%d)" % (SubElementCount, SubElementCount.uint))

	# Read each SubElements
	for i in range(0, SubElementCount.uint):

		p1 = pprint()

		ElementID = b.read("bits:8")
		if not ElementID:
			continue

		p1.print("SubElementID %d : %s (%s)" % (i, ElementID, IA_ELEMENT_NAMES.get(ElementID.uint)))
		ElementSizeBytes = b.read("bits:8").uint
		p1.print("SubElementSize %d : %d bytes" % (i, ElementSizeBytes))
		ElementValue = b.read("bytes:%d" % ElementSizeBytes)
		p1.print("SubElementValue %s" % ElementValue.hex())

		del p1



"""
	===============================================
			IAElement : Audio Data PCM
			   Used only on IAB
			 (not used on Atmos)
	===============================================
"""
def audio_data_pcm_parser(bytes, **kwargs):

	b = ConstBitStream(bytes)
	p = pprint()
	p.main("Audio Data PCM")

	if DEBUG:
		p.print("Buffer = hex(%s)" % ConstBitStream(bytes).hex)
		p.print("Buffer = bin(%s)" % ConstBitStream(bytes).bin)
		p.print("Args   = %s"      % kwargs)

	# --------- Audio Data ID -------------------------------------
	AudioDataID = plex8(b)
	p.print("AudioDataID : %d" % AudioDataID.uint)

	samplecount = SAMPLECOUNTS.get(kwargs.get("SampleRate")).get(kwargs.get("FrameRate"))
	assert samplecount != None, "samplecount is not found"

	for i in range(0, samplecount):

		data = b.read("bits:%d" % kwargs.get("BitDepth"))
		p.print("Sample %8d/%d * %s bits : 0x%s" % (i+1, samplecount, kwargs.get("BitDepth"), data.hex))

		if OUTFILE:
			OUTFILE.write(data.bytes)

	if not DEBUG:
		p.print("")

	p.print("AlignBits(%d)" % b.bytealign())



"""
	===============================================
			  IAElement : Audio Data DLC
				(used on Dolby Atmos)
	===============================================
"""
def audio_data_dlc_parser(bytes, **kwargs):

	b = ConstBitStream(bytes)
	p = pprint()
	p.main("Audio Data DLC")

	if DEBUG:
		p.print("Buffer = hex(%s)" % ConstBitStream(bytes).hex)
		p.print("Buffer = bin(%s)" % ConstBitStream(bytes).bin)
		p.print("Args   = %s"      % kwargs)

	# --------- Audio Data ID -------------------------------------
	AudioDataID = plex8(b)
	p.print("AudioDataID : %d" % AudioDataID.uint)

	# -------- DLC Size -------------------------------------------
	DLCSize = b.read("bits:16")
	p.print("DLCSize : %d bytes" % DLCSize.uint)

	# -------- DLC Sample Rate ------------------------------------
	DLCSampleRate = b.read("bits:2")
	p.print("DLCSampleRate : %s Hz" % SAMPLERATES.get(DLCSampleRate.uint))

	# -------- ShiftBits ------------------------------------------
	ShiftBits = b.read("bits:5")
	p.print("ShiftBits : %s" % ShiftBits.uint)

	# -------- Predictor Informations -----------------------------
	p.print("────── Predictor Informations ─────")
	NumPredRegions = b.read("bits:2")
	p.print("NumPredRegions : %s (%s regions)" % (NumPredRegions, NumPredRegions.uint))

	for i in range(0, NumPredRegions.uint):

		p1 = pprint()
		p1.title("Region n°%d" % i)

		RegionLength = b.read("bits:4")
		p1.print("RegionLength : %s" % RegionLength.uint)

		Order = b.read("bits:5")
		p1.print("Order : %s" % Order.uint)

		# KCoeff
		for j in range(0, Order.uint):
			KCoeff = b.read("bits:10")
			p1.print("KCoeff[%2d] : %s (%d)" % (j+1, KCoeff, KCoeff.uint))

		del p1
	#----------------------------------------------------------------


	# -------- Coded Residual ----------------------------
	p.print("───── Coded Residual ─────")

	# -------- NumSubBlocks ------------------------------
	NumSubBlock = SUB_BLOCK_NUMS.get(kwargs.get('SampleRate')).get(kwargs.get('FrameRate'))
	p.print("NumSubBlock = %s" % NumSubBlock)

	if VERBOSE <= 0:
		return

	# -------- Coded Residual ----------------------------
	for i in range(0, NumSubBlock):

		p.print("───── NumSubBlock n°%d ─────" % i)
		p1 = pprint()

		CodeType = b.read("bits:1")
		p1.print("CodeType : %s (%s)" % (
			CodeType.uint, {
				0:"Direct PCM", 
				1:"Rice-Colomb Coding"
			}.get(CodeType.uint)
			)
		)


		# ==================================================
		#
		#					 Direct PCM
		#
		# ==================================================
		if CodeType.uint == 0:

			p1.print("───── CODE TYPE 0 ─────")

			# ------- BitDepth ----------
			BitDepth = b.read("bits:5")
			p1.print("BitDepth : %s (%s bits)" % (BitDepth, BitDepth.uint))

			# ------ SubBlockSize ---------
			SubBlockSize = SUB_BLOCK_SIZES.get(kwargs.get('SampleRate')).get(kwargs.get('FrameRate'))
			p1.print("SubBlockSize = %s" % SubBlockSize)

			# Residual
			for j in range(0, SubBlockSize):
				Residual = b.read("bits:%d" % BitDepth.uint)
				p1.print("Residual(%s) : %s (%d bits)" % (j, Residual, BitDepth.uint))


		# =================================================
		#
		#				Rice/Golomb Residual
		#
		# =================================================
		else:

			p1.print("───── CODE TYPE 1 ─────")

			# Rice/Colomb Residual
			p1.print("───── RiceColomb Residual ─────")

			RiceRemBits = b.read("bits:5")
			p1.print("RiceRemBits : %s (%d bits)" % (RiceRemBits, RiceRemBits.uint))

			# ------ DLCSubBlockSize48 ---------
			SubBlockSize = SUB_BLOCK_SIZES.get(kwargs.get('SampleRate')).get(kwargs.get('FrameRate'))
			p1.print("SubBlockSize = %s" % SubBlockSize)

			for j in range(0, SubBlockSize):

				quotient = 0

				UnaryBit = b.read("bits:1").uint
				p1.print("UnaryBit[%s] : %s" % (j, UnaryBit))

				while UnaryBit == 1:
					quotient += 1
					UnaryBit = b.read("bits:1").uint
					p1.print("UnaryBit[%s] : %s" % (j, UnaryBit))
				
				p1.print("Quotient : %d" % quotient)

				Residual48 = b.read("bits:%d" % RiceRemBits.uint)
				p1.print("Residual48 : %s (%d bytes)" % (Residual48, RiceRemBits.uint))

				# Residual.uint += quotient << RiceRemBits.uint
		del p1


	if kwargs.get("SampleRate") == 96000:
		p.print("96 kHz - not supported yet")
		return


"""
	===============================
		IAElement : Authoring
	===============================
"""
def authoring_parser(bytes, **kwargs):

	b = ConstBitStream(bytes)
	p = pprint()
	p.main("Authoring")

	if DEBUG:
		p.print("Buffer = hex(%s)" % ConstBitStream(bytes).hex)
		p.print("Buffer = bin(%s)" % ConstBitStream(bytes).bin)
		p.print("Args   = %s"      % kwargs)

	p.print("Authoring Tool URI = \"")
	while True:
		AuthoringToolURI = b.read("bits:8")
		if not AuthoringToolURI:
			break
		p.print("%c" % AuthoringToolURI.uint)
	p.print("\"")


"""
	==========================
	  IAElement : User Data 
	==========================
"""
def user_defined_data_parser(bytes, **kwargs):

	b = ConstBitStream(bytes)
	p = pprint()
	p.main("User Defined Data")

	if DEBUG:
		p.print("Buffer = hex(%s)" % ConstBitStream(bytes).hex)
		p.print("Buffer = bin(%s)" % ConstBitStream(bytes).bin)
		p.print("Args   = %s"      % kwargs)

	UserDataID = b.read("bits:128")
	p.print("UserDataID : %s" % UserDataID.hex)

	while True:
		try:
			UserDataBytes = b.read("bits:8")
			p.print("UserDataBytes : %s" % UserDataBytes)
		except ReadError:
			p.print("UserDataBytes End")
			break

"""
	=================================
		IAElement : Bed Remap
	=================================
"""
def bed_remap_parser(bytes, **kwargs):

	b = ConstBitStream(bytes)
	p = pprint()
	p.main("Bed Remap")

	if DEBUG:
		p.print("Buffer = hex(%s)" % ConstBitStream(bytes).hex)
		p.print("Buffer = bin(%s)" % ConstBitStream(bytes).bin)
		p.print("Args   = %s"      % kwargs)
	
	# ------- MetaID ---------------------------------------------
	MetaID = plex8(b)
	p.print("MetaID : %d" % MetaID.uint)

	# ------ RemapUseCase ----------------------------------------
	RemapUseCase = b.read("bits:8")
	p.print("RemapUseCase = %s (%s)" % (RemapUseCase, USECASES.get(RemapUseCase.uint)))

	# ------ SourceChannels - plex(4) ------------------------------
	SourceChannels = plex4(b)
	p.print("SourceChannels : %s (%d channels)" % (SourceChannels, SourceChannels.uint))

	# ------ DestinationChannels - plex(4) ---------------------------
	DestinationChannels = plex4(b)
	p.print("DestinationChannels : %s (%d channels)" % (DestinationChannels, DestinationChannels.uint))

	# TODO : Create matrix
	NumPanSubBlocks = 8   # SMPTE.RDD.0029-2019 - Dolby Atmos Bitstream Specification, Table 7
	for i in range(0, NumPanSubBlocks):

		if i == 0:
			RemapInfoExists = True
		else:
			RemapInfoExists = bool(b.read("bits:1").uint)

		p.print("RemapInfoExists : %s" % RemapInfoExists)

		if RemapInfoExists:
			for j in range(0, DestinationChannels.uint):

				p.print("───── DestinationChannels %d ─────" % j)

				# ------ DestinationChannelID - plex(4) ------
				DestinationChannelID = plex4(b)
				p.print("DestinationChannelID : %s" % DestinationChannelID.uint)

				for k in range(0, SourceChannels.uint):

					p.print("───── SourceChannel %d ─────" % k)

					RemapGainPrefix = b.read("bits:2")
					p.print("RemapGainPrefix : %s (%s)" % (RemapGainPrefix, GAIN_PREFIX_NAMES.get(RemapGainPrefix.uint)))

					if RemapGainPrefix.uint > 1:
						RemapGain = b.read("bits:10")
						p.print("RemapGain : %s (%d)" % (RemapGain, RemapGain.uint))


	p.print("AlignBits(%d)" % b.bytealign())

	# ------ Reserved - plex(4) --------
	Reserved = plex4(b)
	p.print("Reserved : %s" % Reserved)


"""
	=============================
		IAElement : Unknown
	=============================
"""
def unknown_parser(bytes, **kwargs):

	b = ConstBitStream(bytes)
	p = pprint()
	p.main("Unknown Data")

	if DEBUG:
		p.print("Buffer = hex(%s)" % ConstBitStream(bytes).hex)
		p.print("Buffer = bin(%s)" % ConstBitStream(bytes).bin)
		p.print("Args   = %s"      % kwargs)




####################################
##
##         Main Parser 
##	Read all IABitstream Frames
##
####################################

def bitstream_parser(filename):

	file = ConstBitStream(filename=filename)

	while True:

		p = pprint()
		p.main("IABitstream Frame")

		#########################################
		#
		#				Preamble
		#
		#########################################

		p.title("Preamble")

		# PreambuleTag
		PreambuleTag = file.read("bits:8")
		p.print("PreambuleTag : %s" % PreambuleTag)

		# PreambuleLength
		PreambuleLength = file.read("bits:32")
		p.print("PreambuleLength : %d bytes" % PreambuleLength.uint)

		# PreambuleValue
		PreambuleValue = file.read("bytes:%d" % PreambuleLength.uint)
		p.print("PreambuleValue : %s(...%d bytes...)%s" % (PreambuleValue[0:16].hex(), len(PreambuleValue)-32, PreambuleValue[-16:].hex()))


		########################################
		#
		#				IAFrame
		#
		########################################

		p.title("IAFrame")

		IAFrameTag = file.read("bits:8")
		p.print("IAFrameTag : %s" % IAFrameTag)

		IAFrameLength = file.read("bits:32")
		p.print("IAFrameLength : %s bytes" % IAFrameLength.uint)

		IAFrameValue = file.read("bytes:%d" % IAFrameLength.uint)
		p.print("IAFrameValue : %s(...%d bytes...)%s" % (IAFrameValue[0:16].hex(), len(IAFrameValue)-32, IAFrameValue[-16:].hex()))


		#######################################
		#
		#			IAElement
		#
		#######################################

		p.title("IAElement")
		IAElement = ConstBitStream(IAFrameValue)

		# ElementID
		ElementID = plex8(IAElement)
		p.print("ElementID : %s (%s)" % (ElementID, IA_ELEMENT_NAMES.get(ElementID.uint)))
		
		# ElementSize
		ElementSizeBytes = plex8(IAElement)
		p.print("ElementSize : %s (%d bytes)" % (ElementSizeBytes, ElementSizeBytes.uint))

		# ElementValue
		ElementValue = IAElement.read("bytes:%d" % ElementSizeBytes.uint)
		p.print("SubElementValue : %s(..) (%d bytes)" % (ElementValue[0:32].hex(), len(ElementValue)))

		# Bypass Parser
		if FILTER is not None and FILTER not in IA_ELEMENT_NAMES.get(ElementID.uint, "Unknown Element"):
			continue

		# Execute
		funcname = IA_ELEMENT_PARSERS.get(ElementID.uint, 'unknown_parser')
		try:
			globals()[funcname](
				bytes = ElementValue
			)
		except Exception as error:
			p.print(f"fatal error ({funcname}) : {error}")

		del p

		# Another IABitstream Frame
		if file.pos < file.length:
			print("Another IABistream Frame...\n")
		else:
			print("End of File - no another IABitstream Frame")
			return




# ================================== #
#                                    #
#                MAIN                #
#                                    #
# ================================== #

FILTER  = os.getenv("FILTER")
OUTFILE = os.getenv("OUTFILE")
DEBUG   = os.getenv("DEBUG")
VERBOSE = int(os.getenv("VERBOSE", 0))

if OUTFILE:

	# create header wav
	with wave.open(OUTFILE, "wb") as file:
		file.setnchannels(1)      # 1 channel
		file.setsampwidth(3)      # bit-depth (3 bytes : 24 bits)
		file.setframerate(48000)  # sampling-rate (48kHz)

	OUTFILE = open(OUTFILE, "ab+")

# check args
if len(sys.argv) < 2:
	print("Usage: file.iab or directory contains iab files")
	sys.exit(1)

# Parse one file
if os.path.isfile(sys.argv[1]):
	bitstream_parser(sys.argv[1])
	sys.exit(0)

# Parse directory
for directory in sys.argv[1:]:
	for _, _, files in os.walk(directory):
		for file in sorted(files):
			if "ImmersiveAudioDataElement.value.bin" in file or ".iab" in file:
				print("+++ %s/%s" % (directory, file))
				bitstream_parser("%s/%s" % (directory, file))

if OUTFILE:
	OUTFILE.close()

