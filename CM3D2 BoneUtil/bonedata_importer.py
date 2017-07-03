# -*- coding: utf-8 -*-

import bpy  # type: ignore
import math
import mathutils  # type: ignore
import os
import sys
from . import common
from typing import Dict, Set, List, Tuple, Optional, Any


def menu_func(self, context):  # type: (Any, bpy.types.Context) -> None
	ob = context.active_object
	if not ob or ob.type != 'MESH':
		return
	if ob.parent is None or ob.parent.type != 'ARMATURE':
		return
	if len(ob.parent.data.bones) == 0:
		return
	# MESHの場合は、親がARMATUREであり、ボーンがあることが条件

	menu_func_common(self, context)


def menu_func_arm(self, context):  # type: (Any, bpy.types.Context) -> None
	ob = context.active_object
	if not ob or ob.type != 'ARMATURE':
		return

	menu_func_common(self, context)


def menu_func_common(self, context):  # type: (Any, bpy.types.Context) -> None
	layout = self.layout
	split = layout.split(0.3, align=True)
	split.label(text="butl.bdimport.ImportBoneData4CM3D2", icon='IMPORT')

	label = bpy.app.translations.pgettext('butl.bdimport.ImportBoneData')
	split.operator(CM3D2BoneDataImporter.bl_idname, icon='CONSTRAINT_BONE', text=label)
	label = bpy.app.translations.pgettext('butl.bdimport.RenameBaseBone')
	split.operator(CM3D2BaseBoneRenamer.bl_idname, icon='BONE_DATA', text=label)


class CM3D2BaseBoneRenamer(bpy.types.Operator):  # type: ignore
	bl_idname = 'object.trzr_rename_cm3d2_basebone'
	bl_label = 'Rename BaseBone'
	bl_description = bpy.app.translations.pgettext('butl.bdimport.RenameBaseBoneDesc')
	bl_options = {'REGISTER', 'UNDO'}

	bb_name = bpy.props.StringProperty(name="butl.BaseBoneName")
	change_bonename = bpy.props.BoolProperty(name="butl.RenameBone", default=False)

	def __init__(self):  # type: () -> None
		self.bb_name_old = None  # type: Optional[str]
		self.target_props = None  # type: Any

	@classmethod
	def poll(cls, context):  # type: (bpy.types.Context) -> bool
		ob = context.active_object
		if ob:
			if ob.type == 'ARMATURE':
				return 'BaseBone' in ob.data
			elif ob.type == 'MESH':
				return 'BaseBone' in ob

		return False

	def invoke(self, context, event):  # type: (bpy.types.Context, Any) -> Set
		ob = context.active_object
		self.bb_name = ''
		if ob.type == 'ARMATURE':
			self.bb_name = ob.data['BaseBone']
			self.target_props = ob.data
			self.target_bones = ob.data.bones
			self.is_mesh = False
		elif ob.type == 'MESH':
			self.bb_name = ob['BaseBone']
			self.target_props = ob
			# 親がARMATUREでない場合も動作
			if ob.parent and ob.parent.type == 'ARMATURE':
				self.target_bones = ob.parent.data.bones
			self.is_mesh = True

		self.bb_name_old = self.bb_name
		return context.window_manager.invoke_props_dialog(self)

	def draw(self, context):  # type: (bpy.types.Context) -> None
		self.layout.prop(self, 'bb_name', icon='SORTALPHA')
		# self.layout.prop(self, 'target_type', icon='BONE_DATA')

		if self.target_bones and self.bb_name_old in self.target_bones:
			row = self.layout.row(align=True)
			row.prop(self, 'change_bonename', icon='NONE')

	def execute(self, context):  # type: (bpy.types.Context) -> Set
		ob = context.active_object
		self.bb_name_old = self.target_props['BaseBone']
		if self.bb_name == self.bb_name_old:
			self.report(type={'INFO'}, message="BaseBone was not changed.")
			return {'CANCELLED'}

		target_name = self._rename_prop(self.target_props, self.bb_name)

		if self.change_bonename:
			if self.bb_name_old in self.target_bones:
				self.target_bones[self.bb_name_old].name = self.bb_name
				if self.is_mesh:
					# Armatureのカスタムプロパティもあわせて変更
					prop_name = self._rename_prop(ob.parent.data, self.bb_name)
					if prop_name:
						target_name += "," + prop_name

		if target_name:
			msg = bpy.app.translations.pgettext('butl.bdimport.RenameBaseBoneCompleted')
			self.report(type={'INFO'}, message=msg + ' ' + str(target_name))

		return {'FINISHED'}

	def _rename_prop(self, props, bb_name):  # type: (Dict, str) -> str
		for item in props.items():
			prop_name = item[0]
			if prop_name.startswith('BoneData:'):
				try:
					bonedata_txt = item[1]
					bdlist = bonedata_txt.split(',', 1)
					if len(bdlist) < 1:
						continue

					if self.bb_name_old == bdlist[0]:
						bdlist[0] = bb_name
						props[prop_name] = bdlist[0] + ',' + bdlist[1]
						props['BaseBone'] = bb_name
						return prop_name
						break
				except:
					pass
		return ''


class BoneData1(object):  # type: ignore

	def __init__(self, name, sclflag, parent_name, prop_name):  # type: (str, int, str, str) -> None
		self.sclflag = 0
		self.name = name
		self.is_nub = name.lower().endswith('nub')
		self.sclflag = sclflag
		self.parent_name = parent_name
		self.has_parent = (parent_name != "None")
		self.children = []  # type: List
		self.co = ''
		self.rot = ''
		self.prop_name = prop_name
		self.parent = None
		self.no_exist = False


class CM3D2BoneDataImporter(bpy.types.Operator):  # type: ignore
	bl_idname = 'object.trzr_import_cm3d2_bonedata'
	bl_label       = 'Import BoneData'
	bl_description = bpy.app.translations.pgettext('butl.bdimport.ImportBoneDataDesc')
	bl_options = {'REGISTER', 'UNDO'}

	bb_name       = bpy.props.StringProperty(name="butl.BaseBoneName")
	target_items = [
		('All', 'butl.EnumAll', "", '', 0),
		('Selected', 'butl.EnumSelected', "", '', 1),
		('Descendant', 'butl.EnumDescendant', "", '', 2),
	]
	target_type   = bpy.props.EnumProperty(name="Target", items=target_items, default='Descendant')
	scale         = bpy.props.FloatProperty(name="Scale", default=5, min=0.1, max=100, soft_min=0.1, soft_max=100, step=100, precision=1, description="butl.ScaleDesc")
	import_bd     = bpy.props.BoolProperty(name="BoneData", default=True)
	import_lbd    = bpy.props.BoolProperty(name="LocalBoneData", default=True)
	sync_bd       = bpy.props.BoolProperty(name="butl.bdimport.RemoveBoneDataNonExistent", default=False)
	exclude_ikbd  = bpy.props.BoolProperty(name="butl.bdimport.ExcludeIKBoneDataForRemove", default=True)
	vg_opr = bpy.props.EnumProperty(
		name="VertexGroup",
		items=[
			('add', 'Add', "butl.bdimport.AddVGDesc", 'PLUS', 0),
			('exist', 'butl.bdimport.UseExist', "butl.bdimport.UseExistDesc", 'BLANK1', 1),
		],
		default='exist')
	act_mode = bpy.props.EnumProperty(
		name="ActMode",
		items=[
			('normal', 'butl.bdimport.NormalMode', 'butl.bdimport.NormalModeDesc', 'PROP_CON', 0),
			('auto', 'butl.bdimport.AutoDetect', 'butl.bdimport.AutoDetectDesc', 'PROP_ON', 1),
			('old', 'butl.bdimport.OldMode', 'butl.bdimport.OldModeDesc', 'PROP_OFF', 2),
		], default='normal')

	def __init__(self):  # type: () -> None
		self.is_old        = False

		self.bonedata_idx = 0
		self.bd_dic = {}   # type: Dict
		self.lbd_idx = 0
		self.lbd_dic = {}  # type: Dict

		self.coor = None
		self.rotor = None  # BaseBoneが回転している場合があるため追加 by夜勤D
		self.target_props = None  # type: Any
		self.target_bones = {}   # type: Dict
		# self.target_data = None
		self.bone_names = set()  # type: Set[str]
		self.treated_bones = set()  # type: Set
		self.count_bd_add = 0
		self.count_bd_update = 0
		self.count_lbd_add = 0
		self.count_lbd_update = 0

	@classmethod
	def poll(cls, context):  # type: (bpy.types.Context) -> bool
		ob = context.active_object
		if ob:
			if ob.type == 'ARMATURE':
				if 'BaseBone' in ob.data:
					return True
			elif ob.type == 'MESH':
				if ob.parent and ob.parent.type == 'ARMATURE':
					if 'BaseBone' in ob:
						return True
		return False

	def invoke(self, context, event):  # type: (bpy.types.Context, Any) -> Set
		ob = context.active_object
		if ob.type == 'ARMATURE':
			self.bb_name = ob.data['BaseBone']
			self.target_props = ob.data
			self.target_data = ob.data
			self.target_bones = ob.data.bones
			self.is_mesh = False
		elif ob.type == 'MESH':
			self.bb_name = ob['BaseBone']
			self.target_props = ob
			self.target_data = ob.parent.data
			self.target_bones = ob.parent.data.bones
			self.is_mesh = True

		# 前回が自動判定以外の場合、ボーン情報をチェック
		if self.act_mode != 'auto':
			ret = self.check_old()
			if ret > 0:
				self.act_mode = 'old'
			elif ret == 0:
				self.act_mode = 'normal'

		return context.window_manager.invoke_props_dialog(self)

	def draw(self, context):  # type: (bpy.types.Context) -> None
		self.layout.prop(self, 'bb_name', icon='SORTALPHA')
		self.layout.prop(self, 'target_type', icon='BONE_DATA')

		self.layout.prop(self, 'scale', icon='MAN_SCALE')
		self.layout.label(text="butl.ImportTarget:", icon='IMPORT')
		row = self.layout.row(align=True)
		row.prop(self, 'import_bd', icon='NONE')
		row.prop(self, 'import_lbd', icon='NONE')
		self.layout.prop(self, 'sync_bd', icon='ERROR')
		self.layout.prop(self, 'exclude_ikbd', icon='NONE')

		self.layout.label(text="butl.bdimport.ActionMode:", icon='HAND')
		self.layout.prop(self, 'act_mode', icon='NONE', expand=True)

		ob = context.active_object
		if ob.type == 'MESH':
			self.layout.label(text="butl.VertexGroup:", icon='GROUP_VERTEX')
			self.layout.prop(self, 'vg_opr', icon='NONE', expand=True)

	def execute(self, context):  # type: (bpy.types.Context) -> Set
		self.count_bd_add = 0
		self.count_bd_update = 0
		self.count_lbd_add = 0
		self.count_lbd_update = 0
		self.treated_bones.clear()

		self.bone_names.clear()
		self.is_old = False
		if self.act_mode == 'auto':
			self.is_old = (self.check_old() > 0)
		elif self.act_mode == 'old':
			self.is_old = True

		for target_bone in self.target_bones:
			bone_name = common.remove_serial_num(target_bone.name)
			if bone_name in self.bone_names:
				self.report({'WARNING'}, 'Bone(%s) has skipped because it was already exist.' % target_bone.name)
			else:
				self.bone_names.add(bone_name)

		# 表示状態に設定
		count_bd_del, count_lbd_del = 0, 0
		ob = context.active_object
		src_hide = ob.hide
		ob.hide = False
		if self.is_mesh:
			src_hide_parent = ob.parent.hide
			ob.parent.hide = False

		try:
			self.parse_bonedata()
			# self.bonedata_idx = self.parse_bonedata(self.bd_dic)
			bbdata = self.bd_dic.get(self.bb_name)
			if bbdata is None:
				# TODO BaseBoneのリネーム/変更
				msg = 'BaseBone(%s) not found' % self.bb_name
				self.report(type={'ERROR'}, message=msg)
				return {'CANCELLED'}

			# TODO プロパティから取り込むか、ボーンから取り込むかを選択
			self.coor  = bbdata.co.split(' ')
			self.rotor = bbdata.rot.split(' ')  # BaseBoneが回転している場合があるため追加 by夜勤D

			if ob.mode == 'EDIT':
				bones = self.target_data.edit_bones
			else:
				bones = self.target_data.bones

			if self.target_type == 'Descendant':
				for bone in bones:
					if bone.select:
						self.calc_bonedata(self.target_bones[bone.name], True)
			elif self.target_type == 'Selected':
				for bone in bones:
					if bone.select:
						self.calc_bonedata(self.target_bones[bone.name])
			elif self.target_type == 'All':
				for bone in bones:
					self.calc_bonedata(self.target_bones[bone.name])

			if self.sync_bd:
				# BoneDataの削除
				for bdata1 in self.bd_dic.values():
					if bdata1.no_exist:
						if self.exclude_ikbd and '_IK_' in bdata1.name:
							continue
						if bdata1.is_nub and bdata1.parent_name in self.bone_names:
							continue

						del self.target_props[ bdata1.prop_name ]
						count_bd_del += 1

						lbdata1 = self.lbd_dic.get(bdata1.name)
						if lbdata1:
							del self.target_props[ lbdata1[1] ]
							count_lbd_del += 1

				# LocalBoneDataの削除
				if self.import_lbd:
					for lbd1 in self.lbd_dic.values():
						if not lbd1[3] and lbd1[2] not in self.bone_names:
							del self.target_props[ lbd1[1] ]
							count_lbd_del += 1

				# 歯抜けのBoneData/LocalBoneDataを修正
				if count_bd_del > 0:
					self.reorder_props('BoneData:')
				if count_lbd_del > 0:
					self.reorder_props('LocalBoneData:')
		# except Exception as e:
		# 	self.report(type={'ERROR'}, message="BoneDataの取り込みに失敗しました")
		# 	return {'CANCELLED'}
		# except:
		# 	self.report(type={'ERROR'}, message="Unknown Error")
		# 	return {'CANCELLED'}
		finally:
			self.bd_dic.clear()
			self.lbd_dic.clear()

			# 表示状態を復元
			ob.hide = src_hide
			if self.is_mesh and src_hide_parent:
				ob.parent.hide = src_hide_parent

		# 処理件数を出力する。BoneData数, LocalBoneData数
		if self.is_old:
			msgopt = "[old mode]"
		else:
			msgopt = ""
		logmsg = "TargetCount:%d, BoneData(add:%d,upate:%d,del:%d) LocalBoneData(add:%d,update:%d,del:%d) %s" % (
			len(self.treated_bones),
			self.count_bd_add, self.count_bd_update, count_bd_del,
			self.count_lbd_add, self.count_lbd_update, count_lbd_del,
			msgopt)
		msg = bpy.app.translations.pgettext('butl.bdimport.ImportCompleted') + logmsg
		self.report(type={'INFO'}, message=msg)
		return {'FINISHED'}

	def parse_bonedata(self):  # type: (Any) -> None
		lbd_dic0 = {}
		# BoneData = namedtuple('bonedata', ['name', 'sclflag', 'parent_name', 'prop_name', 'is_nub', 'has_parent', 'children', 'co', 'rot', 'parent'])

		max_bd_idx = 0
		max_lbd_idx = 0
		for item in self.target_props.items():
			prop_name = item[0]
			if prop_name.startswith('BoneData:'):
				try:
					idx = int(prop_name[9:])
					if idx > max_bd_idx:
						max_bd_idx = idx
					bonedata_txt = item[1]

					bdlist = bonedata_txt.split(',')
					if len(bdlist) < 5:
						continue

					bone_name = bdlist[0]
					node = BoneData1(bone_name, bdlist[1], bdlist[2], prop_name)
					node.co  = bdlist[3]
					node.rot = bdlist[4]
					self.bd_dic[bone_name] = node
					if bone_name not in self.bone_names:
						if bone_name != self.bb_name:  # skip BaseBone
							node.no_exist = True
				except:
					pass

			elif prop_name.startswith('LocalBoneData:'):
				try:
					idx = int(prop_name[14:])
					if idx > max_lbd_idx:
						max_lbd_idx = idx
					lbd_txt = item[1]

					bdlist = lbd_txt.split(',')
					if len(bdlist) < 2:
						continue

					lbd_dic0[bdlist[0]] = (prop_name, bdlist[1])
				except:
					pass

		for node in self.bd_dic.values():
			if node.has_parent:
				parent = self.bd_dic.get(node.parent_name)
				if parent is not None:
					parent.children.append(node)
					node.parent = parent

		i = 0
		for lbd_item in lbd_dic0.items():
			exist_bd = lbd_item[0] in self.bd_dic
			# (index, prop_name, bone_name, exist_bd
			self.lbd_dic[lbd_item[0]] = (i, lbd_item[1][0], lbd_item[1][1], exist_bd)
			i += 1

		self.bonedata_idx = max_bd_idx + 1
		self.lbd_idx = max_lbd_idx + 1

	# BoneData整頓
	def reorder_props(self, prefix):  # type: (str) -> None
		change_items = []
		item_count = 0
		prefix_pos = len(prefix)
		for item in self.target_props.items():
			if item[0].startswith(prefix):
				try:
					idx = int(item[0][prefix_pos:])
					if item_count != idx:
						change_items.append( (item[0], item[1], prefix + str(item_count)) )

					item_count += 1
				except:
					pass

		for rename_item in change_items:
			del self.target_props[rename_item[0]]
			self.target_props[rename_item[2]] = rename_item[1]

		change_items.clear()

	# no_use
	def reorder_lbd(self):  # type: () -> None
		remove_items = []
		change_items = []
		item_count = 0
		prefix = 'LocalBoneData:'
		prefix_pos = len(prefix)
		for item in self.target_props.items():
			if item[0].startswith(prefix):
				lbdlist = item[1].split(',')
				if len(lbdlist) < 2:
					remove_items.append(item[0])
				else:
					bone_name = lbdlist[0]
					if bone_name not in self.target_props.vertex_groups:
						remove_items.append(item[0])
					else:
						try:
							idx = int(item[0][prefix_pos:])
							if item_count != idx:
								change_items.append( (item[0], item[1], prefix + str(item_count)) )

							item_count += 1
						except:
							pass

		for rename_item in change_items:
			del self.target_props[rename_item[0]]
			self.target_props[rename_item[2]] = rename_item[1]

		change_items.clear()

	# 旧版の取り込みデータであるかの判定 (やっつけ)
	# return 1 => 旧版 (0 => 新版, -1 => 不明)
	def check_old(self):  # type: () -> int
		if 'Bip01' in self.target_bones:
			if round(self.target_bones['Bip01'].length - 1.0, 6) == 0:
				return 0
			else:
				return 1
		else:
			for target_bone in self.target_bones:
				if target_bone.parent and len(target_bone.children) == 0:
					# 末端ボーンの長さで判断
					baselength = target_bone.parent.length * 0.5
					if round(target_bone.length - baselength, 6) == 0:
						return 0
					elif round(target_bone.length - 0.1, 6) == 0:
						return 1
		return -1

	def calc_bonedata(self, targetbone, recursive=False):  # type: (Any, Any, bool) -> None
		bone_name = targetbone.name
		bone_d = self.target_bones[bone_name]
		bone_name = common.remove_serial_num(bone_name)
		if bone_name in self.treated_bones:
			return
		is_nub = bone_name.lower().endswith('nub')

		# BoneData
		if self.import_bd:
			if targetbone.parent is None:  # 親無しボーン

				parentbone_name = 'None'
				bone_mat = bone_d.matrix_local
				c0 = bone_mat.to_translation() / self.scale
				c0.x, c0.y, c0.z = -c0.x, c0.z, -c0.y
				bone_v = c0
				r0 = bone_mat.to_quaternion()
				if self.is_old:
					r0 *= mathutils.Quaternion((0, 0, 1), math.radians(90))
					r0.w, r0.x, r0.y, r0.z, = -r0.w, -r0.x, r0.z, -r0.y
				else:
					r1 = mathutils.Euler((0, 0, math.radians(-90)), 'XYZ').to_quaternion()
					r2 = mathutils.Euler((math.radians(-90), 0, 0), 'XYZ').to_quaternion()
					r0 = r0 * r1 * r2
					r0.w, r0.x, r0.y, r0.z = -r0.y, -r0.z, -r0.x, r0.w
				bone_q = r0
			else:
				parentbone_name = common.remove_serial_num(targetbone.parent.name)
				# bone_mat = bone_d.parent.matrix_local.inverted() * bone_d.matrix_local
				# bone_v = bone_mat.to_translation() / self.scale
				# bone_q = bone_mat.to_quaternion()
				bone_v = (bone_d.head_local - bone_d.parent.head_local) * bone_d.parent.matrix_local / self.scale
				bone_q = bone_d.matrix.to_3x3().to_quaternion()
				if self.is_old:
					bone_v.x, bone_v.y, bone_v.z = -bone_v.y, bone_v.z, bone_v.x
					bone_q.w, bone_q.x, bone_q.y, bone_q.z = bone_q.w, bone_q.y, -bone_q.z, -bone_q.x

				else:
					bone_v.x, bone_v.y, bone_v.z = -bone_v.y, -bone_v.x, bone_v.z
					bone_q.w, bone_q.x, bone_q.y, bone_q.z = bone_q.w, bone_q.y, bone_q.x, -bone_q.z

			active_prop_name = ''
			bdata1 = self.bd_dic.get(bone_name)
			if bdata1:
				active_prop_name = bdata1.prop_name
				sclflag = bdata1.sclflag
				self.count_bd_update += 1
			else:
				# not found bonedata. 新規追加BoneData
				self.count_bd_add += 1
				active_prop_name = "BoneData:" + str(self.bonedata_idx)
				self.bonedata_idx += 1
				sclflag = 0

			string_bone = "{0},{1},{2},{3:.17} {4:.17} {5:.17},{6:.17} {7:.17} {8:.17} {9:.17}".format(
				bone_name, sclflag, parentbone_name,
				bone_v.x, bone_v.y, bone_v.z,
				bone_q.w, bone_q.x, bone_q.y, bone_q.z)
			self.target_props[active_prop_name] = string_bone

			# add bonedata "_nub"
			if not is_nub and len(targetbone.children) == 0:
				# 長さが基準のままであればnub不要と判断
				if self.is_old:
					base_length = 0.2 * self.scale if targetbone.parent is None else 0.1
				else:
					base_length = 0.2 * self.scale if targetbone.parent is None else targetbone.parent.length * 0.5

				if round(targetbone.length - base_length, 6) != 0:

					nub_scl = 0
					nub_bonename = None
					add_prop_name = None

					# search BoneData from CustomProperty
					if bdata1 and len(bdata1.children) == 1:
						nub_node = self.bd_dic.get(bdata1.children[0].name)
						if nub_node and nub_node.is_nub:
							nub_bonename = nub_node.name
							nub_scl = nub_node.sclflag
							add_prop_name = nub_node.prop_name
							self.count_bd_update += 1

					if nub_bonename is None:
						self.count_bd_add += 1
						idx = bone_name.rfind('_yure_')
						if idx == -1:
							nub_bonename = bone_name
						else:
							nub_bonename = bone_name.replace('_yure_', '_')

						if nub_bonename.endswith('_'):
							nub_bonename = nub_bonename + 'nub'
						else:
							nub_bonename = nub_bonename + '_nub'

						suf = 1
						while nub_bonename in self.treated_bones:
							nub_bonename = nub_bonename[0:-4] + str(suf) + "_nub"
							suf += 1

					bone_vt = (bone_d.tail_local - bone_d.head_local) * bone_d.matrix_local / self.scale
					bone_qt = bone_d.matrix.to_3x3().to_quaternion()
					if self.is_old:
						bone_vt.x, bone_vt.y, bone_vt.z = -bone_vt.y, bone_vt.z, bone_vt.x
						bone_qt.w, bone_qt.x, bone_qt.y, bone_qt.z = bone_qt.w, bone_qt.y, -bone_qt.z, -bone_qt.x
					else:
						bone_vt.x, bone_vt.y, bone_vt.z = -bone_vt.y, -bone_vt.x, bone_vt.z
						bone_qt.w, bone_qt.x, bone_qt.y, bone_qt.z = bone_qt.w, bone_qt.y, bone_qt.x, -bone_qt.z

					string_bone_nub = "{0},{1},{2},{3:.17} {4:.17} {5:.17},{6:.17} {7:.17} {8:.17} {9:.17}".format(
						nub_bonename, nub_scl, bone_name,
						bone_vt.x, bone_vt.y, bone_vt.z,
						bone_qt.w, bone_qt.x, bone_qt.y, bone_qt.z)

					# print("write:" + active_prop_name)
					if add_prop_name is None:
						add_prop_name = "BoneData:" + str(self.bonedata_idx)
						self.bonedata_idx += 1
					self.target_props[add_prop_name] = string_bone_nub
					self.treated_bones.add(nub_bonename)

		# LocalBoneData (末端ノードとBaseBoneを除く)
		if self.import_lbd and not is_nub and self.bb_name != bone_name:
			lbd_skip = False
			if self.is_mesh:
				if bone_name not in self.target_props.vertex_groups:
					if self.vg_opr == 'exist':
						lbd_skip = True
					else:
						# add vertex_group
						self.target_props.vertex_groups.new(bone_name)

			if not lbd_skip:
				qlb = bone_d.matrix_local.to_quaternion()
				if self.is_old:
					qlb.w, qlb.x, qlb.y, qlb.z = qlb.w, qlb.y, -qlb.z, -qlb.x
					rotate_first = mathutils.Matrix( [[0, 0, -1], [0, 1, 0], [1, 0, 0]] )  # mathutils.Euler((0, math.radians(-90), 0), 'XYZ')
				else:
					qlb.w, qlb.x, qlb.y, qlb.z = qlb.w, qlb.y, qlb.x, -qlb.z
					# rotate_first = mathutils.Euler((math.radians(-90), math.radians(-90), 0), 'XYZ')
					rotate_first = mathutils.Matrix( [[0, 1, 0], [0, 0, 1], [1, 0, 0]] )

				mrbase = mathutils.Quaternion( (float(self.rotor[0]), float(self.rotor[1]), float(self.rotor[2]), float(self.rotor[3])) ).to_matrix()
				mt = mathutils.Vector([bone_d.head_local.x, -bone_d.head_local.z, bone_d.head_local.y]) / self.scale * mrbase

				localbone = mrbase.inverted() * rotate_first * qlb.to_matrix()
				localbone.resize_4x4()
				localbone = mathutils.Matrix([
					[1, 0, 0, 0],
					[0, 1, 0, 0],
					[0, 0, 1, 0],
					[mt.x + float(self.coor[0]), mt.y - float(self.coor[2]), mt.z + float(self.coor[1]), 1] ]) * localbone

				string_localbone = "{0},{1:.17} {2:.17} {3:.17} {4:.17} {5:.17} {6:.17} {7:.17} {8:.17} {9:.17} {10:.17} {11:.17} {12:.17} {13:.17} {14:.17} {15:.17} {16:.17}".format(
					bone_name,
					localbone[0][0], localbone[0][1], localbone[0][2], localbone[0][3],
					localbone[1][0], localbone[1][1], localbone[1][2], localbone[1][3],
					localbone[2][0], localbone[2][1], localbone[2][2], localbone[2][3],
					localbone[3][0], localbone[3][1], localbone[3][2], localbone[3][3])

				active_prop_name1 = ''
				lbdata1 = self.lbd_dic.get(bone_name)
				if lbdata1:
					active_prop_name1 = lbdata1[1]  # tuple(idx, prop_name, old_val)
					self.count_lbd_update += 1
				else:
					# not found LocalBoneData. 新規追加LocalBoneData
					self.count_lbd_add += 1
					active_prop_name1 = "LocalBoneData:" + str(self.lbd_idx)
					self.lbd_idx += 1

				self.target_props[active_prop_name1] = string_localbone

		self.treated_bones.add(bone_name)

		if recursive:
			for child in targetbone.children:
				# 処理済みボーンは除く
				if common.remove_serial_num(child.name) not in self.treated_bones:
					self.calc_bonedata(child, recursive)
