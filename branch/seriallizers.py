from rest_framework import serializers
from user.serializers import UserSerializer
from .models import Branch, User, Student

class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'branch']

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['id', 'name', 'origin','branch']

class BranchSerializer(serializers.ModelSerializer):
    teachers = TeacherSerializer(many=True)
    students = StudentSerializer(many=True)

    class Meta:
        model = Branch
        fields = ['id', 'name', 'location', 'teachers', 'students', 'admin_user']

    def create(self, validated_data):
        teachers_data = validated_data.pop('teachers', [])
        students_data = validated_data.pop('students', [])

        branch = Branch.objects.create(**validated_data)

        for teacher_data in teachers_data:
            User.objects.create(branch=branch, **teacher_data)

        for student_data in students_data:
            Student.objects.create(branch=branch, **student_data)

        return branch

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.location = validated_data.get('location', instance.location)
        instance.admin_user = validated_data.get('admin_user', instance.admin_user)
        
        teachers_data = validated_data.get('teachers', [])
        students_data = validated_data.get('students', [])

        # Remove existing teachers not in the updated list
        current_teacher_ids = instance.teachers.values_list('id', flat=True)
        updated_teacher_ids = [teacher_data.get('id') for teacher_data in teachers_data if 'id' in teacher_data]
        teachers_to_remove = current_teacher_ids.exclude(id__in=updated_teacher_ids)
        User.objects.filter(id__in=teachers_to_remove).delete()

        # Update or create teachers in the updated list
        for teacher_data in teachers_data:
            teacher_id = teacher_data.get('id')
            if teacher_id:
                teacher = User.objects.filter(branch=instance, id=teacher_id).first()
                if teacher:
                    teacher.name = teacher_data.get('name', teacher.name)
                    teacher.save()
            else:
                User.objects.create(branch=instance, **teacher_data)

        # Remove existing students not in the updated list
        current_student_ids = instance.students.values_list('id', flat=True)
        updated_student_ids = [student_data.get('id') for student_data in students_data if 'id' in student_data]
        students_to_remove = current_student_ids.exclude(id__in=updated_student_ids)
        Student.objects.filter(id__in=students_to_remove).delete()

        # Update or create students in the updated list
        for student_data in students_data:
            student_id = student_data.get('id')
            if student_id:
                student = Student.objects.filter(branch=instance, id=student_id).first()
                if student:
                    student.name = student_data.get('name', student.name)
                    student.save()
            else:
                Student.objects.create(branch=instance, **student_data)

        instance.save()
        return instance

    def destroy(self, instance):
        # Delete all related teachers and students
        instance.teachers.all().delete()
        instance.students.all().delete()

        # Delete the branch itself
        instance.delete()
